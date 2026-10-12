"""下载官方公开页面，保留采集快照和照片归属；不会上传或发布。"""
from pathlib import Path
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import json, hashlib

ROOT=Path(__file__).resolve().parent
SOURCES={
 'profile':'https://www.wtatennis.com/players/328120/qinwen-zheng',
 'rankings':'https://www.wtatennis.com/players/328120/qinwen-zheng/stats',
 'record':'https://www.wtatennis.com/players/328120/qinwen-zheng/record',
 'beijing2026':'https://www.wtatennis.com/news/4590546/zheng-qinwen-makes-history-with-china-open-wta-1000-title',
 'beijing_route':'https://www.wtatennis.com/news/4589836/mirra-andreeva-vs-zheng-qinwen-everything-to-know-about-china-open-beijing-final',
 'withdrawal2026':'https://www.wtatennis.com/news/4590575/zheng-qinwen-mirra-andreeva-to-miss-wuhan-open-after-beijing-final',
 'olympics':'https://www.wtatennis.com/news/4074958/zheng-holds-off-vekic-in-olympic-gold-medal-final',
 'palermo2023':'https://www.wtatennis.com/news/3601535/zheng-qinwen-beats-paolini-to-capture-first-career-title-in-palermo',
 'zhengzhou2023':'https://www.wtatennis.com/news/3738449/zheng-qinwen-triumphs-on-home-soil-to-claim-zhengzhou-title',
 'palermo2024':'https://www.wtatennis.com/news/4064127/zheng-battles-past-muchova-to-successfully-defend-palermo-title',
 'tokyo2024':'https://www.wtatennis.com/news/4156950/zheng-powers-past-kenin-in-tokyo-wins-third-title-of-year',
 'year2024':'https://www.wtatennis.com/news/4166962/by-the-numbers-the-2024-year-end-rankings/',
 'year2022':'https://www.wtatennis.com/news/2898840/by-the-numbers-the-2022-year-end-rankings',
 'surgery':'https://www.wtatennis.com/news/4317789/zheng-undergoes-elbow-surgery-withdraws-from-us-open',
 'asian_games':'https://oca.asia/news/4373-chinas-zheng-rolls-to-tennis-gold-with-straight-sets-win-over-zhu.html',
 'olympic_draw':'https://www.wtatennis.com/tournaments/650/olympics/2024/draws',
 'olympic_qf':'https://www.wtatennis.com/news/4072161/zheng-rallies-at-olympics-to-end-kerbers-career',
 'olympic_sf':'https://www.wtatennis.com/news/4073042/zheng-shocks-no1-swiatek-to-reach-olympic-gold-medal-final',
 'finals2024':'https://www.wtatennis.com/news/4165822/gauff-overcomes-zheng-in-three-hour-thriller-to-win-title-at-wta-finals',
}
def get(url):
 return urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=40).read()
def collect(item):
 key,url=item
 try:
  raw=get(url); soup=BeautifulSoup(raw,'html.parser')
  for el in soup(['script','style','nav','footer']): el.decompose()
  target=ROOT/'采集快照'; target.mkdir(exist_ok=True)
  (target/(key+'.txt')).write_text(soup.get_text('\n',strip=True),encoding='utf-8')
  imgs=[{'alt':im.get('alt',''),'url':im.get('src','')} for im in soup.select('img') if 'zheng' in im.get('alt','').lower()]
  return {'id':key,'url':url,'accessed':'2026-10-12','title':soup.title.get_text() if soup.title else '', 'sha256':hashlib.sha256(raw).hexdigest(),'images':imgs,'ok':True}
 except Exception as e:
  return {'id':key,'url':url,'accessed':'2026-10-12','ok':False,'error':type(e).__name__}
if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=5) as ex: rows=list(ex.map(collect,SOURCES.items()))
 (ROOT/'数据'/'来源索引.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps([{'id':x['id'],'ok':x['ok'],'images':x.get('images',[])[:2]} for x in rows],ensure_ascii=False,indent=2))
