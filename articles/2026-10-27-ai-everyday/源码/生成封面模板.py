from pathlib import Path

INK, TEAL, CLAY, BG = "#213638", "#166B72", "#BD5B42", "#F9F7F2"

def cover_template(square=False):
    w, h = (1200, 1200) if square else (1800, 766)
    tx, ty, fs = (96, 175, 108) if square else (100, 260, 108)
    gx, gy, scale = (310, 560, 1.05) if square else (1130, 150, 1)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
    <rect width="{w}" height="{h}" fill="{BG}"/>
    <circle cx="{w-110}" cy="{h-100}" r="310" fill="#E7EEEA"/>
    <g font-family="Microsoft YaHei, sans-serif" font-weight="700">
      <text x="{tx}" y="{ty}" font-size="{fs}" fill="{TEAL}">普通人用AI</text>
      <text x="{tx}" y="{ty+150}" font-size="{fs}" fill="{CLAY}">可以做什么？</text>
      <text x="{tx}" y="{ty+238}" font-size="36" fill="{INK}" font-weight="400">36个全场景案例 · 建议收藏</text>
    </g>
    <g transform="translate({gx} {gy}) scale({scale})">
      <rect x="0" y="80" width="490" height="300" rx="20" fill="{TEAL}"/>
      <rect x="18" y="100" width="454" height="250" rx="6" fill="white"/>
      <path d="M-25 390 H515 L545 420 H-55 Z" fill="#75628E"/>
      <rect x="45" y="-10" width="180" height="220" rx="8" fill="#F3DFD1" transform="rotate(-10 45 -10)"/>
      <g stroke="{CLAY}" stroke-width="10"><path d="M70 35H180 M65 75H190 M60 115H180"/></g>
      <rect x="280" y="-45" width="150" height="240" rx="20" fill="#75628E" transform="rotate(8 280 -45)"/>
      <circle cx="355" cy="65" r="45" fill="#F2CF8D"/>
      <path d="M345 40 L380 65 L345 90 Z" fill="white"/>
      <g font-family="Microsoft YaHei, sans-serif" font-size="27" fill="{INK}">
      <text x="52" y="285">文章 · 图表 · 网站 · 视频</text></g>
    </g></svg>'''

if __name__ == "__main__":
    root=Path(__file__).resolve().parent.parent
    for square in (False,True):
        label="方版" if square else "横版"
        (root / "配图" / ("封面模板_"+label+".svg")).write_text(cover_template(square),encoding="utf8")
