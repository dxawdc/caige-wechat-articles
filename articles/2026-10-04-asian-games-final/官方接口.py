"""官方成绩JSON读取；兼容gzip、zlib和站点字符集转换后的压缩内容。"""
from pathlib import Path
from datetime import datetime, timezone
import gzip
import hashlib
import json
import time
import urllib.request
import zlib

ROOT=Path(__file__).resolve().parent
RAW=ROOT/'数据/官方原始'
RAW.mkdir(parents=True,exist_ok=True)
BASE='https://back.results.asiangames2026.org/s/AG2026/en'
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))

def decode(raw):
    candidates=[raw]
    if raw.startswith(b'\x1f\x8b'):candidates.append(gzip.decompress(raw))
    for data in list(candidates):
        try:candidates.append(data.decode('utf-8').encode('latin-1'))
        except (UnicodeDecodeError,UnicodeEncodeError):pass
    for data in candidates:
        try:return json.loads(data.decode('utf-8'))
        except (UnicodeDecodeError,json.JSONDecodeError):pass
        for mode in [zlib.MAX_WBITS,-zlib.MAX_WBITS,zlib.MAX_WBITS|16]:
            try:return json.loads(zlib.decompress(data,mode).decode('utf-8'))
            except (zlib.error,UnicodeDecodeError,json.JSONDecodeError):pass
    raise ValueError('官方响应无法解码，不能将失败请求当成空成绩')

def get(path,name=None):
    url=BASE+path
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0',
              'Accept':'application/json','Accept-Encoding':'gzip',
              'Origin':'https://results.asiangames2026.org','Referer':'https://results.asiangames2026.org/'})
            with opener.open(req,timeout=25) as response:
                raw=response.read()
            result=decode(raw)
            if name:
                content=json.dumps(result,ensure_ascii=False,indent=2).encode('utf-8')
                (RAW/(name+'.json')).write_bytes(content)
                (RAW/(name+'.来源.json')).write_text(json.dumps({'url':url,
                    'fetched_at':datetime.now(timezone.utc).isoformat(),
                    'sha256':hashlib.sha256(content).hexdigest()},ensure_ascii=False,indent=2),encoding='utf-8')
            return result
        except Exception:
            if attempt==2:raise
            time.sleep(attempt+1)
