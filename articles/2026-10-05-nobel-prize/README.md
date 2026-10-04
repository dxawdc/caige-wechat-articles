# 125年诺贝尔奖数据观察

版本：v1.0.0。更新：2026-10-05。

提供1901—2025年诺贝尔奖及经济学纪念奖的官方开放数据、统计CSV、14张图表、封面、首尾品牌动图及采集分析源码。奖金部分另提供2026年9月18日已公布的名义金额。

## 数据与口径

- `数据/原始/laureates.json`：官方API获奖主体信息，1,018个ID；990位个人、28个组织。
- `数据/原始/prizes.json`：官方API奖项信息，682个学科年份，其中633个已颁奖、49个未颁奖。
- `数据/整理/获奖记录.csv`：1,026条获奖记录，每条为一个获奖主体在某年某学科获得奖项；995条个人、31条组织。
- `数据/整理/出生地国家排名.csv`：以现今出生地地域归并国家，个人ID去重。987人有国家信息，3人缺失，共81个国家；原始地点和映射另表提供。
- `数据/整理/高校排名.csv`：获奖时任职机构的个人ID去重人数；校内院系归并、加州大学按校区拆分、明确前身归并。每位获奖者可归属多所学校。
- `数据/整理/高校机构名称归并.csv`：每个原始机构名、城市和归并后名称，可逐行审核。
- `数据/整理/奖金历史.csv`：1901—2025共125年完整奖项名义金额、统一2025年币值金额，单位瑞典克朗。
- `数据/整理/2026年已公布奖金.csv`：2026年每个完整奖项1,200万瑞典克朗，公告日期2026-09-18。
- 性别统计以个人获奖记录为分母；获奖年龄为获奖年份12月10日的周岁，975条生日完整、20条缺失。
- 共享奖项统计以学科年份奖项为分母，包含和平奖组织；经济学自1969年加入。

统计保留官方已列入的获奖记录，包含拒领者与延后颁发的奖项；年份采用`awardYear`。首次获奖人数、获奖记录数、颁奖次数分别统计。

## 复现方法

本次实测环境：Windows、Python 3.14、pandas、Matplotlib。Python 3.10+可使用，建议虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -X utf8 采集数据.py
.\.venv\Scripts\python -X utf8 分析数据.py
.\.venv\Scripts\python -X utf8 生成图表.py
.\.venv\Scripts\python -X utf8 生成封面.py
```

`采集数据.py`默认复用同目录官方快照。需要重新采集时，删除准备更新的原始源文件再运行。分析默认截止2025年，修改`CUTOFF`时同步更新年份范围与官方总数核验。

中文图表使用Windows微软雅黑字体`C:/Windows/Fonts/msyh.ttc`；其他系统可设置`NOBEL_CN_FONT`指向可用中文字体。结果输出到`配图/`，核验输出到`验收/`。CSV为UTF-8 BOM格式，可用Excel直接打开。

`生成封面.py`单独输出`配图/封面.png`，1600×680像素、约2.35:1，用于公众号横版封面。封面以1901—2025年奖金购买力为主题，对比当年名义金额与按2025年币值折算的金额。正文奖金图保留原有版式。

## 数据源

1. 官方获奖者API：https://api.nobelprize.org/2.1/laureates?limit=2000
2. 官方奖项API：https://api.nobelprize.org/2.1/nobelPrizes?limit=2000
3. 官方开奖日程：https://www.nobelprize.org/prizes/about/prize-announcement-dates/
4. 官方历史奖金表：https://www.nobelprize.org/uploads/2026/04/prize-amounts-2025.pdf
5. 2026年奖金公告：https://www.nobelpeaceprize.org/presse/pressemeldinger/the-nobel-prize-is-increased-by-sek-1-million
6. 地图底图：https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_admin_0_countries.geojson
7. 洛克菲勒大学历史归并依据：https://www.rockefeller.edu/about/history/

API数据遵循官方CC0开放数据条款：https://www.nobelprize.org/about/terms-of-use-for-api-nobelprize-org-and-data-nobelprize-org/ 。Natural Earth底图为公共领域地理数据，采用Mollweide投影；小岛使用官方经纬度补充。

官方API与奖金PDF部分实际币值不同：2018年文学奖涉及延后颁发，2024年六个学科API折算值与新版PDF有差别。本组奖金趋势统一使用2025年币值版PDF，同期名义金额全部一致；详细差异保留在`验收/数据核验.json`。

## 更多可复用维度

当前整理数据还可以绘制：每年各学科获奖人次、累计获奖曲线、国家×学科矩阵、任职机构所在国家、出生地→任职地流向、年度年龄中位数、各学科单人/多人共享比例、奖金份额分布和未颁奖年份热力图。

研究培养路径可进一步补教育经历；研究成果产生地可补发现时间和发现机构；国籍榜需逐人核验历史国籍。指标定义和扩展方向见`指标口径.md`。
