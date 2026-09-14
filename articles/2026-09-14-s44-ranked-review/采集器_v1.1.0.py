"""版本 v1.1.0 | 更新 2026-09-14 | 状态：已验证。
当前 MuMu 登录账号的只读战绩采集；会话凭据只在内存中使用。
"""
import base64,io,json,logging,sqlite3,subprocess,time,uuid,struct,zipfile,re,sys
from datetime import datetime,timezone,timedelta
from pathlib import Path
import javaobj,httpx,os,argparse
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher,algorithms
from cryptography.hazmat.decrepit.ciphers.modes import CFB

logging.disable(logging.CRITICAL)
ADB=os.environ.get('MUMU_ADB','adb')
DEVICE=os.environ.get('MUMU_DEVICE','127.0.0.1:16384')
OUT=Path(__file__).parent/'采集输出_私有_v1.0.0'
APK=None
TZ=timezone(timedelta(hours=8))
PUBLIC_KEY='MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC0h62mV/zjJtFsNdfFNlxksfUOpjDI2KCcBrPiA8T7szABT4InLDTrdXAW84QyGNiazB0i7pgPCNGSAYbiJrCRutZ5jQsVS0Wg/RnXfwVQDJcAHJDjP5IXyroeLX7NUxDai8nPcpfRsvq6sneobyPexZSH0TlVSnecsJZTj5wu/wIDAQAB'

def adb_read(path):
    return subprocess.check_output([ADB,'-s',DEVICE,'exec-out','cat',path])

def account():
    db=sqlite3.connect(':memory:')
    db.deserialize(adb_read('/data/data/com.tencent.gamehelper.smoba/databases/AccountDatabase'))
    blob=db.execute('select bytes from account').fetchone()[0]
    off=blob.find(b'\xac\xed\x00\x05')
    return javaobj.JavaObjectUnmarshaller(io.BytesIO(blob[off:])).readObject(ignore_remaining_data=True)

def varint(b,p):
    value=shift=0
    while p<len(b):
        x=b[p];p+=1;value|=(x&127)<<shift
        if not x&128:return value,p
        shift+=7
        if shift>63:raise ValueError('Invalid varint')
    raise ValueError('Incomplete varint')

def user_key(a):
    from loguru import logger
    logger.remove()
    from androguard.core.dex import DEX
    apk=APK
    with zipfile.ZipFile(apk) as z:
        d=DEX(z.read('classes6.dex'))
    key=None
    for c in d.get_classes():
        if c.get_name()=='Lcom/tencent/MmvWrapper/MmkvWrapper;':
            for m in c.get_methods():
                if m.get_name()=='c':
                    for i in m.get_instructions():
                        if i.get_name().startswith('const-string'):
                            key=i.get_string().encode()[:16].ljust(16,b'\0');break
    if key is None:raise RuntimeError('Storage key unavailable')
    path='/data/data/com.tencent.gamehelper.smoba/files/mmkv/camp_login_security_sp'
    b=adb_read(path);meta=adb_read(path+'.crc');size=struct.unpack_from('<I',b)[0]
    dec=Cipher(algorithms.AES(key),CFB(meta[12:28])).decryptor()
    raw=dec.update(b[4:4+size])+dec.finalize()
    _,p=varint(raw,0);values={}
    while p<len(raw):
        n,p=varint(raw,p);k=raw[p:p+n].decode();p+=n
        n,p=varint(raw,p);v=raw[p:p+n];p+=n;values[k]=v
    value=values['camp_login_security_user_key_'+str(a.userId)]
    n,p=varint(value,0)
    return value[p:p+n]

def tea_decrypt(raw,key):
    v=list(struct.unpack('<%dI'%(len(raw)//4),raw));k=list(struct.unpack('<4I',key[:16].ljust(16,b'\0')))
    n=len(v)-1;delta=0x9e3779b9;q=6+52//len(v);s=(q*delta)&0xffffffff;y=v[0]
    while s:
        e=(s>>2)&3
        for p in range(n,-1,-1):
            z=v[p-1] if p else v[n]
            mx=(((z>>5 ^ y<<2)+(y>>3 ^ z<<4)) ^ ((s^y)+(k[(p&3)^e]^z)))&0xffffffff
            v[p]=(v[p]-mx)&0xffffffff;y=v[p]
        s=(s-delta)&0xffffffff
    length=v[-1];b=struct.pack('<%dI'%len(v),*v)
    if length>len(b)-4:raise ValueError('Response decrypt failed')
    return b[:length]

SECRET=re.compile(r'token|cookie|password|secret|openid|encodeparam|encoderes|userkey|^sig$|^pfkey$',re.I)
def clean(obj):
    if isinstance(obj,dict):return {k:clean(v) for k,v in obj.items() if not SECRET.search(k)}
    if isinstance(obj,list):return [clean(v) for v in obj]
    return obj

def save(path,obj):
    path.write_text(json.dumps(clean(obj),ensure_ascii=False,indent=2),encoding='utf8')

class Client:
    def __init__(self):
        self.a=account();self.key=user_key(self.a)
        db=sqlite3.connect(':memory:');db.deserialize(adb_read('/data/data/com.tencent.gamehelper.smoba/databases/RoleDatabase'))
        self.role=db.execute('select roleId from role_scene where gameId=20001 and scene=3').fetchone()[0]
        self.http=httpx.Client(timeout=35);self.previous=0;self.requests=0
    def post(self,path,body):
        for attempt in range(3):
            time.sleep(max(0,0.85-(time.monotonic()-self.previous)))
            self.previous=time.monotonic();self.requests+=1
            try:
                r=self.http.post('https://kohcamp.qq.com'+path,headers=headers(self.a),json=body)
                r.raise_for_status()
                if r.headers.get('encryptparamerr'):raise RuntimeError('Session security check failed')
                j=json.loads(tea_decrypt(base64.b64decode(r.content),self.key)) if r.headers.get('campencrypt')=='true' else r.json()
                code=j.get('returnCode',0)
                if code not in (0,200):raise RuntimeError(f'API returnCode={code}: {j.get("returnMsg", "")}')
                return j
            except (httpx.TransportError,httpx.HTTPStatusError):
                if attempt==2:raise
                time.sleep(2*(attempt+1))

def identity(x):return '|'.join(str(x.get(k,'')) for k in ('gameSvrId','relaySvrId','gameSeq','battleType'))

def collect():
    c=Client();print('SESSION_READY',flush=True)
    raw=OUT/'接口原始数据_v1.0.0';raw.mkdir(exist_ok=True)
    details=raw/'对局详情';details.mkdir(exist_ok=True)
    meta={'version':'v1.0.0','started_at':datetime.now(TZ).isoformat(),'status':'collecting','role_id':c.role,
          'source':'https://kohcamp.qq.com','list_pages':0,'list_complete':False,'detail_success':0,'detail_failures':[],
          'pagination_stop_reason':None,'credentials_saved':False,'request_interval_seconds':0.85}
    try:
        profile=c.post('/game/koh/profile',{'targetUserId':str(c.a.userId),'targetRoleId':c.role,'resVersion':'3','recommendPrivacy':'0','apiVersion':'2'})
        save(raw/'当前角色主页_v1.0.0.json',profile)
        # Preserve only the requested role in the user-facing metadata.
        meta['role']=next((r for r in profile['data'].get('roleList',[]) if str(r.get('roleId'))==c.role),{})
        rows=[];seen=set();cursor=0
        for page in range(1,1001):
            payload=c.post('/game/morebattlelist',{'lastTime':cursor,'recommendPrivacy':0,'apiVersion':5,
                'friendUserId':str(c.a.userId),'friendRoleId':c.role,'option':0})
            save(raw/f'战绩列表_第{page:03d}页_v1.0.0.json',payload)
            d=payload['data'];new=0
            for row in d.get('list',[]):
                k=identity(row)
                if k not in seen:seen.add(k);rows.append(row);new+=1
            meta['list_pages']=page;meta['matches']=len(rows)
            save(OUT/'战绩列表完整_v1.0.0.json',rows);save(OUT/'采集状态_v1.0.0.json',meta)
            print(f'LIST page={page} new={new} total={len(rows)} hasMore={d.get("hasMore")}',flush=True)
            if not d.get('hasMore'):
                meta['list_complete']=True;meta['pagination_stop_reason']='server_hasMore_false';break
            nxt=d.get('lastTime')
            if not new or not nxt or str(nxt)==str(cursor):
                meta['pagination_stop_reason']='pagination_stalled';break
            cursor=nxt
        else:meta['pagination_stop_reason']='safety_page_limit'
        for ep,body,name in [('/game/seasonpage',{'recommendPrivacy':0,'seasonId':0,'roleId':c.role},'赛季统计'),
                             ('/game/evaluationconf',{'recommendPrivacy':0},'评价配置'),
                             ('/game/battleproconf',{'recommendPrivacy':0},'战绩配置')]:
            try:save(raw/f'{name}_v1.0.0.json',c.post(ep,body))
            except Exception as e:print('OPTIONAL_FAILED',ep,type(e).__name__,flush=True)
        for index,row in enumerate(rows,1):
            k=identity(row);name=k.replace('|','_')+'_v1.0.0.json';path=details/name
            if path.exists():
                try:
                    prev=json.loads(path.read_text(encoding='utf8'))
                    if prev.get('returnCode')==0 and prev.get('data',{}).get('head'):
                        meta['detail_success']+=1;continue
                except ValueError:pass
            body={'recommendPrivacy':0,'battleType':row['battleType'],'gameSvr':str(row['gameSvrId']),
                  'relaySvr':str(row['relaySvrId']),'targetRoleId':c.role,'gameSeq':row['gameSeq']}
            try:
                result=c.post('/game/battledetail',body);save(path,result)
                if not result.get('data',{}).get('head'):raise ValueError('Detail lacks head')
                meta['detail_success']+=1
            except Exception as e:
                meta['detail_failures'].append({'match_key':k,'error_type':type(e).__name__,'message':str(e)[:180]})
                print('DETAIL_FAILED',index,type(e).__name__,flush=True)
                if isinstance(e,RuntimeError) and '-30457' in str(e):
                    meta['detail_stop_reason']='server_retention_limit_-30457'
                    meta['detail_retention_message']='暂不支持查看一个月前的战绩详情'
                    meta['detail_missing_older_records']=len(rows)-meta['detail_success']
                    meta['status']='complete_with_source_limits'
                    break
                if isinstance(e,RuntimeError):raise
            if index%10==0 or index==len(rows):
                save(OUT/'采集状态_v1.0.0.json',meta)
                print(f'DETAIL {index}/{len(rows)} success={meta["detail_success"]}',flush=True)
        if meta['status']!='complete_with_source_limits':meta['status']='collected'
    except Exception as e:
        meta['status']='incomplete';meta['error_type']=type(e).__name__;meta['error']=str(e)[:200]
        print('COLLECTION_STOPPED',type(e).__name__,flush=True)
    finally:
        meta['finished_at']=datetime.now(TZ).isoformat();meta['request_count']=c.requests
        save(OUT/'采集状态_v1.0.0.json',meta)
        print('DONE',meta['status'],'matches',meta.get('matches',0),'details',meta['detail_success'],flush=True)

def headers(a):
    ts=int(time.time()*1000)
    nonce=json.dumps({'timestamp':ts,'nonce':f':{uuid.uuid4().hex}:{ts}'},separators=(',',':')).encode()
    pub=serialization.load_der_public_key(base64.b64decode(PUBLIC_KEY))
    return {'Content-Type':'application/json; charset=UTF-8','User-Agent':'okhttp/4.9.1',
        'NOENCRYPT':'1','X-Client-Proto':'https','istrpcrequest':'true','cchannelid':'10003391',
        'cclientversioncode':'2057973408','cclientversionname':'10.114.0826','ccurrentgameid':'20001',
        'cgameid':'20001','cgzip':'1','cisarm64':'true','crand':str(ts),'csupportarm64':'true',
        'csystem':'android','csystemversioncode':'35','csystemversionname':'15','gameid':'20001',
        'token':str(a.userToken),'userid':str(a.userId),'openid':str(a.openId),
        'specialEncodeParam':base64.b64encode(pub.encrypt(nonce,padding.PKCS1v15())).decode()}

def probe():
    a=account()
    key=user_key(a)
    print('session_decryption_ready',bool(key))
    with httpx.Client(timeout=25) as client:
        r=client.post('https://kohcamp.qq.com/game/morebattlelist',headers=headers(a),json={
            'lastTime':0,'recommendPrivacy':0,'apiVersion':5,'friendUserId':str(a.userId),'option':0})
        print('HTTP',r.status_code,'bytes',len(r.content),'flags',{k:v for k,v in r.headers.items() if k.lower() in ['returncode','campencrypt','encryptparamerr']})
        try:
            j=json.loads(tea_decrypt(base64.b64decode(r.content),key)) if r.headers.get('campencrypt')=='true' else r.json()
            print('top_keys',list(j));print('returnCode',j.get('returnCode'),'returnMsg',j.get('returnMsg'))
            d=j.get('data',j);print('data_keys',list(d)[:80])
            if isinstance(d,dict) and isinstance(d.get('list'),list):
                print('rows',len(d['list']),'hasMore',d.get('hasMore'))
                if d['list']:print('row_keys',list(d['list'][0]))
                save(OUT/'战绩列表首批_v1.0.0.json',j)
        except ValueError:print('non_json_response')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='读取本人已登录 MuMu 会话；不自动开启 root。')
    parser.add_argument('--adb',default=ADB)
    parser.add_argument('--device',default=DEVICE)
    parser.add_argument('--apk',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=OUT)
    parser.add_argument('--collect',action='store_true')
    args=parser.parse_args();ADB=args.adb;DEVICE=args.device;APK=args.apk;OUT=args.output
    OUT.mkdir(parents=True,exist_ok=True)
    collect() if args.collect else probe()
