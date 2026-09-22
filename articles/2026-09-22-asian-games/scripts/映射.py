# -*- coding: utf-8 -*-
"""2026 爱知·名古屋亚运会 —— 中英文映射表与统一绘图样式。

官方成绩系统只提供英文名称，本模块负责：
  1. 59 个比赛项目 英文 -> 中文
  2. 46 个参赛代表团 英文/代码 -> 中文
  3. 场馆城市 英文 -> 中文
  4. 统一的 matplotlib 中文样式与配色
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- 项目
DISC_ZH = {
    "BK3": "三人篮球", "ARC": "射箭", "GAR": "竞技体操", "SWA": "花样游泳",
    "ATH": "田径", "BDM": "羽毛球", "BBL": "棒球", "BKB": "篮球",
    "VBV": "沙滩排球", "BOX": "拳击", "BKG": "霹雳舞", "CSL": "皮划艇激流回旋",
    "CSP": "皮划艇静水", "CKT": "板球", "BMF": "自由式小轮车", "BMX": "小轮车竞速",
    "MTB": "山地自行车", "CRD": "公路自行车", "CTR": "场地自行车", "DIV": "跳水",
    "EQU": "马术", "ELS": "电子竞技", "FEN": "击剑", "FBL": "足球",
    "GLF": "高尔夫球", "HBL": "手球", "HOC": "曲棍球", "JJI": "柔术",
    "JUD": "柔道", "KAB": "卡巴迪", "KTE": "空手道", "KUR": "库拉什",
    "MMA": "综合格斗", "MPN": "现代五项", "PDL": "板式网球", "GRY": "艺术体操",
    "ROW": "赛艇", "RU7": "七人制橄榄球", "SAL": "帆船帆板", "SPK": "藤球",
    "SHO": "射击", "SKB": "滑板", "TST": "软式网球", "SBL": "垒球",
    "CLB": "运动攀岩", "SQU": "壁球", "SRF": "冲浪", "SWM": "游泳",
    "TTE": "乒乓球", "TKW": "跆拳道", "TEN": "网球", "TEQ": "台克球",
    "GTR": "蹦床", "TRI": "铁人三项", "VVO": "排球", "WPO": "水球",
    "WLF": "举重", "WRE": "摔跤", "WSU": "武术",
}

# ---------------------------------------------------------------- 代表团
ORG_ZH = {
    "AFG": "阿富汗", "ART": "亚洲难民队", "BAN": "孟加拉国", "BHU": "不丹",
    "BRN": "巴林", "BRU": "文莱", "CAM": "柬埔寨", "CHN": "中国",
    "HKG": "中国香港", "INA": "印度尼西亚", "IND": "印度", "IRI": "伊朗",
    "IRQ": "伊拉克", "JOR": "约旦", "JPN": "日本", "KAZ": "哈萨克斯坦",
    "KGZ": "吉尔吉斯斯坦", "KOR": "韩国", "KSA": "沙特阿拉伯", "KUW": "科威特",
    "LAO": "老挝", "LBN": "黎巴嫩", "MAC": "中国澳门", "MAS": "马来西亚",
    "MDV": "马尔代夫", "MGL": "蒙古", "MYA": "缅甸", "NEP": "尼泊尔",
    "OMA": "阿曼", "PAK": "巴基斯坦", "PHI": "菲律宾", "PLE": "巴勒斯坦",
    "PRK": "朝鲜", "QAT": "卡塔尔", "SGP": "新加坡", "SRI": "斯里兰卡",
    "SYR": "叙利亚", "THA": "泰国", "TJK": "塔吉克斯坦", "TKM": "土库曼斯坦",
    "TLS": "东帝汶", "TPE": "中国台北", "UAE": "阿联酋", "UZB": "乌兹别克斯坦",
    "VIE": "越南", "YEM": "也门",
}

# 官方英文全称 -> 代码（用于把长名归一）
ORG_EN2CODE = {
    "People's Republic of China": "CHN", "China": "CHN",
    "Hong Kong, China": "HKG", "Macao, China": "MAC",
    "Chinese Taipei": "TPE", "Republic of Korea": "KOR", "Korea": "KOR",
    "DPR Korea": "PRK", "Islamic Republic of Iran": "IRI", "IR Iran": "IRI",
    "Saudi Arabia": "KSA", "UA Emirates": "UAE",
    "Syrian Arab Republic": "SYR", "Syria": "SYR",
    "Brunei Darussalam": "BRU", "Lao PDR": "LAO", "Viet Nam": "VIE",
}

# ---------------------------------------------------------------- 城市
CITY_ZH = {
    "Nagoya": "名古屋", "Tokoname": "常滑", "Toyota": "丰田", "Toyohashi": "丰桥",
    "Okazaki": "冈崎", "Tokyo": "东京", "Shizuoka": "静冈", "Anjo": "安城",
    "Gamagori": "蒲郡", "Gifu": "岐阜", "Kasugai": "春日井", "Aisai": "爱西",
    "Tokai": "东海", "Komaki": "小牧", "Hekinan": "碧南", "Tahara": "田原",
    "Miyoshi": "三好", "Shinshiro": "新城", "Nissin": "日进", "Nishio": "西尾",
    "Ichinomiya": "一宫", "Inazawa": "稻泽", "Kariya": "刈谷", "Osaka": "大阪",
}

# ---------------------------------------------------------------- 选手
# 只收录有权威媒体中文名的运动员（新华社 / 央视 / 腾讯等报道口径）；
# 没有把握的一律保留官方英文名，不自行音译。
ATHLETE_ZH = {
    "TANG Qianting": "唐钱婷", "XU Jiayu": "徐嘉余", "YU Zidi": "于子迪",
    "PENG Xuwei": "彭旭玮", "SHENG Lihao": "盛李豪", "WANG Zifei": "王子菲",
    "PAN Zhanle": "潘展乐", "LI Bingjie": "李冰洁", "ZHANG Zhanshu": "张展硕",
    "DONG Zhihao": "董志豪", "LI Liuchang": "李刘畅",
    "People's Republic of China": "中国队",
    "China": "中国队",
}


def athlete(name):
    return ATHLETE_ZH.get((name or "").strip(), (name or "").strip())


# ---------------------------------------------------------------- 奖牌
MEDAL_ZH = {"ME_GOLD": "金牌", "ME_SILVER": "银牌", "ME_BRONZE": "铜牌"}
MEDAL_SHORT = {"ME_GOLD": "金", "ME_SILVER": "银", "ME_BRONZE": "铜"}
C_GOLD, C_SILVER, C_BRONZE = "#D9A21B", "#9AA6B2", "#B87333"
C_MEDAL = {"ME_GOLD": C_GOLD, "ME_SILVER": C_SILVER, "ME_BRONZE": C_BRONZE}
# 金银铜按顺序取色（CSV 里是 金/银/铜 三列，用中文键）
C_MEDAL_ZH = {"金": C_GOLD, "银": C_SILVER, "铜": C_BRONZE}


def disc(code):
    return DISC_ZH.get(code, code)


def org(code):
    """接受代码或英文全称，返回中文名。"""
    if code in ORG_ZH:
        return ORG_ZH[code]
    c = ORG_EN2CODE.get(code)
    if c:
        return ORG_ZH[c]
    return code


def org_code(name):
    if name in ORG_ZH:
        return name
    return ORG_EN2CODE.get(name, name)


def city(name):
    return CITY_ZH.get(name, name)


# ---------------------------------------------------------------- 样式
PALETTE = ["#2F6FED", "#C8102E", "#D9A21B", "#0E9F6E", "#8B5CF6",
           "#EC7C26", "#0EA5E9", "#64748B", "#DB2777", "#65A30D",
           "#0F766E", "#9333EA"]
TEXT = "#1F2733"
GRID = "#DCE3EC"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHART_DIR = os.path.join(ROOT, "图表")


def apply_style():
    plt.rcParams.update({
        "font.sans-serif": ["Microsoft YaHei", "Noto Sans SC", "SimHei"],
        "font.family": "sans-serif",
        "axes.unicode_minus": False,
        "figure.dpi": 110,
        "savefig.dpi": 160,
        "savefig.bbox": "tight",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": GRID,
        "axes.labelcolor": TEXT,
        "axes.titlesize": 15,
        "axes.titleweight": "bold",
        "axes.titlecolor": TEXT,
        "axes.labelweight": "normal",
        "text.color": TEXT,
        "xtick.color": TEXT,
        "ytick.color": TEXT,
        "xtick.labelsize": 10.5,
        "ytick.labelsize": 10.5,
        "legend.frameon": False,
        "legend.fontsize": 10.5,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "grid.alpha": 1.0,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.autolayout": False,
    })


def save(fig, name, dpi=None):
    os.makedirs(CHART_DIR, exist_ok=True)
    p = os.path.join(CHART_DIR, name)
    fig.savefig(p, facecolor="white", **({"dpi": dpi} if dpi else {}))
    plt.close(fig)
    return p
