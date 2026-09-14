"""v1.0.0: collect the public review list, no login/cookies or private profiles.
Raw files are local research inputs; do not commit them to the public repository.
"""
import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from urllib.request import Request, urlopen

BASE = 'https://www.taptap.cn'

def fetch(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0',
                              'Referer': BASE + '/app/243110/review'})
    for attempt in range(3):
        try:
            with urlopen(req, timeout=30) as response:
                return response.read()
        except HTTPError as exc:
            # Do not retry rate limits, authentication or challenge responses.
            if exc.code not in (500, 502, 503, 504):
                raise RuntimeError(f'HTTP {exc.code}; stop and inspect access conditions') from None
            if attempt == 2:
                raise
            time.sleep(3 * (attempt + 1))
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(3 * (attempt + 1))

def first_url(page):
    match = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>',
                      page.decode('utf-8'), re.S)
    if not match:
        raise RuntimeError('No public Nuxt page data; stop, do not bypass challenge')
    flat = json.loads(match.group(1))
    sample = next(x for x in flat if isinstance(x, str)
                  and '/review/v2/list-by-app?X-UA=' in x)
    query = parse_qs(urlparse(sample).query, keep_blank_values=True)
    query.update(sort=['new'], limit=['10'], **{'from': ['0']})
    return BASE + '/webapiv2/review/v2/list-by-app?' + urlencode(query, doseq=True)

def crawl(output, max_pages=600, delay=1.2):
    output.mkdir(parents=True, exist_ok=True)
    checkpoint = output / 'checkpoint_v1.0.0.json'
    if checkpoint.exists():
        state = json.loads(checkpoint.read_text(encoding='utf8'))
        if state.get('completed'):
            print('Completed cache exists; use a new folder for a new snapshot.')
            return
    else:
        page = fetch(BASE + '/app/243110/review')
        (output / 'landing_v1.0.0.html').write_bytes(page)
        start = first_url(page)
        state = {'started_at': datetime.now(timezone.utc).isoformat(),
                 'next_url': start, 'xua': parse_qs(urlparse(start).query)['X-UA'][0],
                 'pages': 0, 'completed': False, 'totals_reported': [], 'page_hashes': []}
    while state['pages'] < max_pages and state['next_url']:
        url = state['next_url']
        parts = urlparse(url)
        if parts.hostname != 'www.taptap.cn' or parts.path != '/webapiv2/review/v2/list-by-app':
            raise RuntimeError('Unexpected next_page target')
        payload = fetch(url)
        obj = json.loads(payload)
        if obj.get('success') is not True:
            raise RuntimeError('API returned failure; stop without bypass')
        data = obj['data']
        rows = data.get('list', [])
        n = state['pages']
        (output / f'page_{n:04d}_v1.0.0.json').write_bytes(payload)
        state['pages'] += 1
        state['totals_reported'].append(data.get('total'))
        state['page_hashes'].append(hashlib.sha256(payload).hexdigest())
        nxt = data.get('next_page')
        if not nxt or not rows:
            state['next_url'] = ''
            state['completed'] = True
        else:
            absolute = urljoin(BASE, nxt)
            p = urlparse(absolute)
            q = parse_qs(p.query, keep_blank_values=True)
            q['X-UA'] = [state['xua']]
            state['next_url'] = BASE + p.path + '?' + urlencode(q, doseq=True)
            if state['next_url'] == url:
                raise RuntimeError('Repeated pagination URL; stop')
        state['updated_at'] = datetime.now(timezone.utc).isoformat()
        checkpoint.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf8')
        if state['pages'] % 20 == 0 or state['completed']:
            print(f"pages={state['pages']} total={data.get('total')} complete={state['completed']}", flush=True)
        if not state['completed']:
            time.sleep(max(delay, 1.0))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-pages', type=int, default=600)
    args = parser.parse_args()
    crawl(args.output, args.max_pages)
