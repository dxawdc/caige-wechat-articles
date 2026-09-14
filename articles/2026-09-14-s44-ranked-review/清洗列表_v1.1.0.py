"""v1.1.0 | 2026-09-15 | 核心列表清洗，并从本人详情提取牌子编码。
不伪造详情。原始123列完整快照继续保留；此脚本是文章复现的精简入口。
"""
import argparse,csv,json,re
from pathlib import Path
from datetime import datetime,timedelta,timezone

def main():
    p=argparse.ArgumentParser();p.add_argument('--list',type=Path,required=True)
    p.add_argument('--mapping',type=Path,required=True);p.add_argument('--heroes',type=Path,required=True)
    p.add_argument('--details',type=Path);p.add_argument('--role-id',default=None)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    rows=read(a.list);mapping=read(a.mapping)['mapping'];names={int(x['ename']):x['cname'] for x in read(a.heroes)}
    metadata=a.list.parent/'采集状态_v1.0.0.json'
    role=str(a.role_id or (read(metadata).get('role_id','') if metadata.exists() else ''))
    thresholds=[(0,'最强王者'),(10,'非凡王者'),(20,'无双王者'),(30,'绝世王者'),(40,'至圣王者'),(50,'荣耀王者'),(100,'传奇王者')]
    badges={1:'金牌上路',2:'银牌上路',3:'金牌中路',4:'银牌中路',5:'金牌发育路',6:'银牌发育路',7:'金牌打野',8:'银牌打野',9:'金牌游走',10:'银牌游走'}
    tz=timezone(timedelta(hours=8));result=[]
    for r in rows:
        code,stars=int(r['roleJob']),int(r['stars']);info=mapping[str(code)]
        if info['previousStars']>=100:
            group='王者';name=next(n for t,n in reversed(thresholds) if stars>=t)
        else:
            short=info['name'];group=next(g for g in ['青铜','白银','黄金','铂金','钻石','星耀'] if g in short)
            name={'钻石':'永恒钻石','星耀':'至尊星耀'}.get(group,group)+short[len(group):]
        key='|'.join(str(r[k]) for k in ['gameSvrId','relaySvrId','gameSeq','battleType'])
        end=datetime.fromtimestamp(int(r['dtEventTime']),tz);start=end-timedelta(seconds=int(r['usedTime']))
        detail_status='未导入详情';head={};badge_code=None
        if a.details:
            path=a.details/(key.replace('|','_')+'_v1.0.0.json')
            if path.exists():
                detail=read(path).get('data',{});head=detail.get('head',{})
                if head:detail_status='已采集'
                own=next((x for x in detail.get('blueRoles',[])+detail.get('redRoles',[]) if role and str(x.get('basicInfo',{}).get('roleId',''))==role),{})
                badge_code=own.get('battleStats',{}).get('branchEvaluateType')
        result.append({'开局时间':start.strftime('%Y-%m-%d %H:%M:%S'),'结束时间':end.strftime('%Y-%m-%d %H:%M:%S'),
            '模式':re.sub(r'\s*(单排|双排|三排|五排)$','',head.get('mapName',r['mapName'])),'历史段位':name,'历史段位含星':f'{name} {stars}星','段位大类':group,
            '段位编码_列表':code,'星数_列表':stars,'组队人数':r['teamNum'],'英雄':names[int(r['heroId'])],
            '结果':'胜利' if r['gameresult']==1 else '失败','击杀':r['killcnt'],'死亡':r['deadcnt'],'助攻':r['assistcnt'],
            '时长秒':r['usedTime'],'胜方MVP原值':r['mvpcnt'],'败方MVP原值':r['losemvp'],
            '评分':r['gradeGame'],'牌子':badges.get(r['branchEvaluate'],''),'对局评价':head.get('matchDesc',r.get('desc','')) or '',
            '详情状态':detail_status,'分路牌子编码_详情':badge_code,'对局唯一键':key})
    if a.output.exists():raise FileExistsError('请选新的输出路径以保留旧版。')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
    print('cleaned rows',len(result))

if __name__=='__main__':main()
