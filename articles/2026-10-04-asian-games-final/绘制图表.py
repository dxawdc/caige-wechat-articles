"""使用随包快照离线重建全部图表；从任何工作目录调用均可。"""
import runpy
from pathlib import Path
from 整理数据 import main as clean
from 采集地区 import main as regions
from 整理选手指标 import main as athletes

ROOT=Path(__file__).resolve().parent
clean(); regions(); athletes()
for filename in ['01_代表团榜单.py','02_地区榜单.py','03_地区金牌地图.py',
                 '04_项目热力矩阵.py','05_中国金牌项目.py','06_累计金牌.py',
                 '08_代表团金牌地图.py','09_选手金牌榜.py','10_年龄分布.py',
                 '11_性别分布.py','12_破纪录项目分布.py','绘制封面.py']:
    runpy.run_path(str(ROOT/filename),run_name='__main__')
print('十一张正文图与独立封面生成完成。')
