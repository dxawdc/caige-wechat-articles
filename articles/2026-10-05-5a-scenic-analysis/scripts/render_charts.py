"""重绘电脑端8张3840×2160图。"""
import sys
from chart_design import render_desktop, report
sys.stdout.reconfigure(encoding='utf-8')
if __name__=='__main__':
    render_desktop();report()
