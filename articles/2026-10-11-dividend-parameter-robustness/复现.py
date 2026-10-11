"""离线冻结快照复算：校验总回报构建、回测账本，生成6张图。"""
from pathlib import Path
import json,math,contextlib,io,runpy
BASE=Path(__file__).resolve().parent
data=json.loads((BASE/'数据/总回报行情.json').read_text(encoding='utf-8'))
for code,fund in data.items():
    factor=1.;dates=[]
    for r in fund['rows']:
        dates.append(r['date']);assert r['market_open']>0 and r['market_close']>0
        factor*=1+r['dividend']/r['market_open']
        assert math.isclose(factor,r['reinvestment_factor'],rel_tol=1e-12)
        assert math.isclose(factor*r['market_open'],r['open'],rel_tol=1e-12)
        assert math.isclose(factor*r['market_close'],r['close'],rel_tol=1e-12)
    assert dates==sorted(set(dates))
import 回测研究
with contextlib.redirect_stdout(io.StringIO()):回测研究.main()
runpy.run_path(str(BASE/'验收回测.py'),run_name='__main__')
import 绘制图表
绘制图表.article_b()
print('冻结快照复算与独立账本核验通过，6张图已更新。')
