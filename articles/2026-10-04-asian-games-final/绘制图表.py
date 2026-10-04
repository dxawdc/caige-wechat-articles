"""使用随包快照离线重建全部图表；从任何工作目录调用均可。"""
import runpy
from pathlib import Path
from 整理数据 import main as clean
from 采集地区 import main as regions

ROOT=Path(__file__).resolve().parent
clean(); regions()
for filename in ['01_代表团榜单.py','02_地区榜单.py','03_地区金牌地图.py',
                 '04_项目热力矩阵.py','05_中国金牌项目.py','06_累计金牌.py','绘制封面.py']:
    runpy.run_path(str(ROOT/filename),run_name='__main__')
print('六张正文图与独立封面生成完成。')
