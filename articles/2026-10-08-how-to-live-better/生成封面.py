"""生成横版(1800×766)与方版(1200×1200)可编辑SVG封面，并用本机Chrome无头渲染PNG。

封面不放账号署名，主文案为“高性价比人生指南”。主体是按真实条目数据排列的672格华夫图：颜色=换回什么，深浅=性价比档。
"""
from pathlib import Path
import subprocess
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '封面'
OUT.mkdir(exist_ok=True)
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

BG, INK, MUTED, CARD = '#F6F2EA', '#1F2A2E', '#7B8186', '#FFFDF8'
LENS = {'换寿命': '#C2553F', '换钱': '#C9962F', '换时间精力': '#3B8A7A', '换人身自由': '#3A5878'}
ORDER = list(LENS)
TIER = {'极高': 1.0, '高': .5, '一般': .18}
FONT = "'Noto Sans SC','Microsoft YaHei',sans-serif"

df = pd.read_csv(ROOT / '数据' / '条目.csv', dtype={'钱': str})
df = df.assign(o=df.口径名.map({k: i for i, k in enumerate(ORDER)}), t=df.性价比.map({'极高': 0, '高': 1, '一般': 2})).sort_values(['o', 't'])
assert len(df) == 672


def mix(hex_color, a):
    c = [int(hex_color[i:i + 2], 16) for i in (1, 3, 5)]
    w = [int(CARD[i:i + 2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(a * x + (1 - a) * y):02X}' for x, y in zip(c, w))


def waffle(x0, y0, cols, cell, gap):
    out = ['<g id="waffle">']
    for i, r in enumerate(df.itertuples()):
        cx, cy = i % cols, i // cols
        out.append(f'<rect x="{x0 + cx * cell}" y="{y0 + cy * cell}" width="{cell - gap}" height="{cell - gap}" rx="{(cell - gap) * .22:.1f}" fill="{mix(LENS[r.口径名], TIER[r.性价比])}"/>')
    out.append('</g>')
    return '\n'.join(out)


def legend(x, y, size):
    parts = []
    for k in ORDER:
        label = k[1:]
        parts.append(f'<rect x="{x}" y="{y - size * .8}" width="{size * .8}" height="{size * .8}" rx="4" fill="{LENS[k]}"/>'
                     f'<text x="{x + size * 1.15}" y="{y}" font-size="{size}" fill="{INK}">{label}</text>')
        x += size * (1.15 + len(label)) + size * 1.4
    return '\n'.join(parts)


def horizontal():
    W, H = 1800, 766
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">
<rect width="{W}" height="{H}" fill="{BG}"/>
<rect x="124" y="128" width="84" height="12" fill="{LENS['换寿命']}"/>
<text id="主文案1" x="116" y="300" font-size="148" font-weight="700" fill="{INK}">高性价比</text>
<text id="主文案2" x="116" y="460" font-size="148" font-weight="700" fill="{LENS['换寿命']}">人生指南</text>
<text id="副文案" x="122" y="560" font-size="46" font-weight="700" fill="{INK}" fill-opacity=".78">到底教人怎么过日子？</text>
{legend(124, 650, 30)}
<rect x="1060" y="70" width="640" height="626" rx="28" fill="{CARD}" stroke="#E3DCCF" stroke-width="2"/>
{waffle(1093, 138, 28, 20.6, 4)}
</svg>'''
    return svg, W, H


def square():
    W, H = 1200, 1200
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">
<rect width="{W}" height="{H}" fill="{BG}"/>
<rect x="110" y="100" width="76" height="11" fill="{LENS['换寿命']}"/>
<text id="主文案1" x="100" y="270" font-size="150" font-weight="700" fill="{INK}">高性价比</text>
<text id="主文案2" x="100" y="430" font-size="150" font-weight="700" fill="{LENS['换寿命']}">人生指南</text>
<text id="副文案" x="106" y="520" font-size="50" font-weight="700" fill="{INK}" fill-opacity=".78">怎么过日子？</text>
<rect x="110" y="580" width="980" height="530" rx="30" fill="{CARD}" stroke="#E3DCCF" stroke-width="2"/>
{waffle(310, 600, 28, 20.6, 4)}
</svg>'''
    return svg, W, H


for name, (svg, W, H) in {'封面横版': horizontal(), '封面方版': square()}.items():
    p = OUT / f'{name}.svg'
    p.write_text(svg, encoding='utf-8')
    html = OUT / f'_{name}.html'
    html.write_text(f'<html><body style="margin:0">{svg}</body></html>', encoding='utf-8')
    png = OUT / f'{name}.png'
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', f'--window-size={W},{H}',
                    f'--screenshot={png}', html.as_uri()], check=True, capture_output=True)
    html.unlink()
    print('saved', png)
