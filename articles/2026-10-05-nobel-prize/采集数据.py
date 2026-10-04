"""采集诺贝尔奖官方API和辅助地理数据；默认保留2025年前完整年份。"""
from pathlib import Path
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib, json, time

ROOT = Path(__file__).resolve().parent
RAW = ROOT / '数据' / '原始'
RAW.mkdir(parents=True, exist_ok=True)
RECEIPT=ROOT/'数据'/'来源记录.json'
PREVIOUS={r['file']:r for r in json.loads(RECEIPT.read_text(encoding='utf8'))} if RECEIPT.exists() else {}
SOURCES = {
    'laureates.json': 'https://api.nobelprize.org/2.1/laureates?limit=2000',
    'prizes.json': 'https://api.nobelprize.org/2.1/nobelPrizes?limit=2000',
    'countries_v1.json': 'https://api.nobelprize.org/v1/country.json',
    'money.html': 'https://www.nobelprize.org/prizes/about/the-nobel-prize-money/',
    'announcements.html': 'https://www.nobelprize.org/prizes/about/prize-announcement-dates/',
    'world.geojson': 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson',
    'prize-amounts-2025.pdf': 'https://www.nobelprize.org/uploads/2026/04/prize-amounts-2025.pdf',
    'prize-money-2026.html': 'https://www.nobelpeaceprize.org/presse/pressemeldinger/the-nobel-prize-is-increased-by-sek-1-million',
}

def fetch(item):
    name, url = item
    target = RAW / name
    if target.exists():
        b = target.read_bytes()
        previous=PREVIOUS.get(name,{})
        return {**previous,'file': name, 'url': url, 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(), 'cached': True,'retrieved_at':previous.get('retrieved_at',datetime.fromtimestamp(target.stat().st_mtime,timezone.utc).isoformat())}
    for attempt in range(3):
        try:
            request = Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'})
            with urlopen(request, timeout=45) as response:
                b = response.read()
            target.write_bytes(b)
            print(name, len(b), flush=True)
            return {'file': name, 'url': url, 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(), 'retrieved_at': datetime.now(timezone.utc).isoformat()}
        except Exception as exc:
            if attempt == 2:
                print(name, str(exc), flush=True)
                return {'file': name, 'url': url, 'error': str(exc)}
            time.sleep(1 + attempt)

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(fetch, SOURCES.items()))
    RECEIPT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    if (RAW / 'money.html').exists():
        from bs4 import BeautifulSoup
        soup = BeautifulSoup((RAW / 'money.html').read_text(encoding='utf-8'), 'html.parser')
        for a in soup.select('a[href]'):
            href = a['href']
            if '.pdf' in href and ('amount' in href or 'prize' in href):
                print('PDF', href, a.get_text(strip=True), flush=True)
