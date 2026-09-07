"""v1.0.0 | 2026-09-07 | 默认离线自测；--online 才发送一次计费 API 请求。"""
import argparse,getpass,json,os,threading
from http.server import BaseHTTPRequestHandler,HTTPServer
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

MODELS=['deepseek-v4-flash','deepseek-v4-pro','deepseek-v4-flash-vision-exp']
def request(key,model,url='https://api.deepseek.com/responses'):
    body={'model':model,'input':'只输出 CODEX_DEEPSEEK_OK，不要添加解释。','reasoning':{'effort':'low'},'max_output_tokens':256,'stream':False}
    with urlopen(Request(url,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'}),timeout=60) as r:response=json.load(r)
    text=''.join(c.get('text','') for item in response.get('output',[]) if item.get('type')=='message' for c in item.get('content',[]) if c.get('type')=='output_text')
    return {'status':response.get('status'),'returnedModel':response.get('model'),'markerReceived':'CODEX_DEEPSEEK_OK' in text,'inputTokens':response.get('usage',{}).get('input_tokens'),'outputTokens':response.get('usage',{}).get('output_tokens'),'scope':'只验证一次文本 Responses 请求，不证明桌面工具链全部可用。'}

def self_test():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            assert self.path=='/responses' and body['model']=='deepseek-v4-flash'
            assert self.headers['Authorization']=='Bearer sk-your-key'
            data=json.dumps({'model':body['model'],'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'CODEX_DEEPSEEK_OK'}]}],'usage':{'input_tokens':9,'output_tokens':6}}).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(data)
    server=HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        r=request('sk-your-key','deepseek-v4-flash',f'http://127.0.0.1:{server.server_port}/responses')
        assert r['markerReceived'] and r['status']=='completed'
    finally:server.shutdown();server.server_close();thread.join()
    return {'passed':True,'liveDeepSeekRequest':False,'test':'本地模拟 HTTP：请求路径、模型、鉴权头与响应文本解析'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--online',action='store_true');p.add_argument('--model',choices=MODELS,default=MODELS[0]);a=p.parse_args()
    if not a.online:result=self_test()
    else:
        key=os.environ.get('DEEPSEEK_API_KEY') or getpass.getpass('DeepSeek API Key（不回显）：')
        if not key or key=='sk-your-key':raise SystemExit('请提供有效 Key；占位符不可用于线上请求。')
        try:result=request(key,a.model)
        except HTTPError as e:raise SystemExit(f'HTTP {e.code}：检查凭据、额度、模型与请求参数；未打印响应正文或 Key。')
        except (URLError,TimeoutError):raise SystemExit('网络连接失败或超时；未打印凭据。')
        result['liveDeepSeekRequest']=True
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if a.online and not(result['status']=='completed' and result['markerReceived']):raise SystemExit(1)
