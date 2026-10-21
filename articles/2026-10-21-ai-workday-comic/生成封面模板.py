"""生成可编辑横版、方版SVG模板；文本与全部几何形状独立，可在Inkscape中导出PNG。"""
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '配图'
ROOT.mkdir(exist_ok=True)

def visual(x, y, scale):
    return f'''<g id="task-illustration" transform="translate({x},{y}) scale({scale})" stroke="#202532" stroke-width="8" stroke-linejoin="round">
<circle cx="570" cy="100" r="68" fill="#FFE7A0"/><path d="M570 55v45l28 18" fill="none" stroke-linecap="round"/>
<rect x="60" y="100" width="340" height="105" rx="20" fill="white"/><circle cx="110" cy="151" r="23" fill="#25B576" stroke="none"/><path d="m99 151 8 8 17-19" fill="none" stroke="white" stroke-width="7"/><rect x="158" y="138" width="185" height="25" rx="12" fill="#B6A5EF" stroke="none"/>
<rect x="170" y="230" width="390" height="245" rx="18" fill="#465064"/><rect x="190" y="250" width="350" height="195" rx="8" fill="#FBFAFF" stroke="none"/>
<rect x="215" y="278" width="290" height="25" rx="10" fill="#B6A5EF" stroke="none"/><rect x="215" y="325" width="225" height="25" rx="10" fill="#25B576" stroke="none"/><rect x="215" y="372" width="260" height="25" rx="10" fill="#FFCA72" stroke="none"/>
<path d="M170 475h390l60 60H110z" fill="#D9DCE6"/><path d="M300 497h110l18 22H282z" fill="#AEB5C6" stroke-width="4"/>
</g>'''

for name, w, h, square in [('横版', 1800, 766, False), ('方版',1200,1200,True)]:
    if square:
        tx, y1, y2, fs, art = 88, 190, 350, 118, visual(170,470,1.25)
        panel = '<path d="M0 650 1200 420v780H0z" fill="#DCD6FF"/>'
    else:
        tx, y1, y2, fs, art = 110, 295, 465, 132, visual(980,100,1.05)
        panel = '<path d="M1020 0h780v766H860z" fill="#DCD6FF"/>'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><title>有了AI，怎么更忙了？｜可编辑{name}封面模板</title><rect width="{w}" height="{h}" fill="#FFF8E8"/>{panel}<g id="cover-copy" fill="#202532" font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif" font-weight="900"><text id="headline-line-1" x="{tx}" y="{y1}" font-size="{fs}">有了AI</text><text id="headline-line-2" x="{tx}" y="{y2}" font-size="{fs}">怎么更忙了？</text></g>{art}</svg>'''
    (ROOT / f'封面模板_{name}.svg').write_text(svg, encoding='utf-8')
print('SVG templates ready: 1800x766 and 1200x1200')
