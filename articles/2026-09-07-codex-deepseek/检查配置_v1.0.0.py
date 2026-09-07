"""v1.0.0 | 2026-09-07 | Python 3.11+；只读配置检查，不输出 Key。"""
from pathlib import Path
import argparse,json,os,tomllib,tempfile
from urllib.parse import urlsplit

MODELS={'deepseek-v4-flash','deepseek-v4-pro','deepseek-v4-flash-vision-exp'}
def inspect(path):
    problems=[]
    try:config=tomllib.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError,ValueError):return {'ok':False,'problems':['配置无法读取或 TOML 语法错误；检查重复键、引号和文件编码。']}
    model=config.get('model');provider=config.get('model_provider')
    item=config.get('model_providers',{}).get(provider,{})
    if model not in MODELS:problems.append('model 不是本文核验的三个 DeepSeek 模型 ID。')
    if not item:problems.append('找不到 model_provider 对应的服务商配置。')
    url=urlsplit(item.get('base_url',''))
    if (url.scheme,url.hostname,url.path.rstrip('/'))!=('https','api.deepseek.com','') or url.query or url.fragment:
        problems.append('直连 base_url 应为 https://api.deepseek.com，不能写到 /responses 或 /chat/completions。')
    if item.get('wire_api','responses')!='responses':problems.append('wire_api 应为 responses。')
    methods=[bool(item.get(k)) for k in ('env_key','experimental_bearer_token','auth')]
    if sum(methods)!=1:problems.append('应明确配置一种凭据来源，避免混用。')
    if item.get('requires_openai_auth'):problems.append('DeepSeek 直连不使用 requires_openai_auth=true。')
    key_source='environment' if methods[0] else 'inline' if methods[1] else 'command' if methods[2] else 'missing'
    available=bool(os.environ.get(item.get('env_key',''))) if methods[0] else methods[1] or methods[2]
    if methods[0] and not available:problems.append('当前进程没有读到 env_key 指定的环境变量；桌面进程需另行验证。')
    pointer=config.get('model_catalog_json')
    catalog_ok=False
    try:
        if not isinstance(pointer,str):raise ValueError()
        catalog_path=Path(pointer).expanduser()
        if not catalog_path.is_absolute():raise ValueError()
        models=json.loads(catalog_path.read_text(encoding='utf-8-sig'))['models']
        selected=next(m for m in models if m['slug']==model)
        if model.endswith('vision-exp') and 'image' not in selected.get('input_modalities',[]):raise ValueError()
        catalog_ok=True
    except (OSError,ValueError,KeyError,StopIteration,TypeError):
        problems.append('模型目录路径、JSON、模型条目或图像能力声明不匹配。建议用官方脚本生成并使用绝对路径。')
    return {'ok':not problems,'model':model if model in MODELS else '(unsupported)','providerDefined':bool(item),'credentialSource':key_source,'credentialAvailableToThisProcess':bool(available),'catalogEntryFound':catalog_ok,'problems':problems,'scope':'仅静态检查；不验证 Key 有效性、桌面进程环境或实际工具调用。'}

def self_test():
    with tempfile.TemporaryDirectory(prefix='caige-deepseek-check-') as tmp:
        base=Path(tmp);catalog=base/'models.json';config=base/'config.toml'
        catalog.write_text(json.dumps({'models':[{'slug':'deepseek-v4-flash','input_modalities':['text']}]}),encoding='utf-8')
        valid=f'model="deepseek-v4-flash"\nmodel_provider="deepseek"\nmodel_catalog_json={json.dumps(catalog.as_posix())}\n[model_providers.deepseek]\nname="DeepSeek"\nbase_url="https://api.deepseek.com"\nwire_api="responses"\nexperimental_bearer_token="sk-your-key"\n'
        tests=[]
        for label,value,expected in [('valid',valid,True),('bad_endpoint',valid.replace('https://api.deepseek.com','https://api.deepseek.com/responses'),False),('wrong_model',valid.replace('model="deepseek-v4-flash"','model="deepseek-v3"'),False),('duplicate_key','model="x"\n'+valid,False),('missing_catalog',valid.replace(catalog.as_posix(),(base/'absent.json').as_posix()),False),('mixed_auth',valid+'env_key="CAIGE_TEST_MISSING_KEY"\n',False)]:
            config.write_text(value,encoding='utf-8');r=inspect(config);assert r['ok']==expected,label
            assert 'sk-your-key' not in json.dumps(r);tests.append(label)
    return {'passed':True,'cases':tests,'liveRequest':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path);p.add_argument('--self-test',action='store_true');a=p.parse_args()
    if a.self_test:result=self_test()
    elif a.config:result=inspect(a.config)
    else:p.error('请选择 --config 文件路径 或 --self-test')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result.get('passed',result.get('ok')) else 1)
