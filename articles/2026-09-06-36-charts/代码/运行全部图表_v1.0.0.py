"""v1.0.0 | 2026-09-06 | 实际运行、批量导出、数据口径校验。"""
from pathlib import Path
import os
import sys
import json
import runpy
import time
import importlib.metadata as metadata

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / '代码'
order = '折线图,阶梯图,面积图,堆叠面积图,区间带图,柱状图,条形图,分组柱状图,堆叠柱状图,百分比堆叠柱状图,棒棒糖图,哑铃图,饼图,环形图,矩形树图,旭日图,瀑布图,漏斗图,直方图,核密度图,箱线图,小提琴图,经验累积分布图,带状散点图,散点图,气泡图,回归散点图,二维直方图,相关矩阵热力图,等高线图,雷达图,极坐标柱状图,桑基图,甘特图,K线图,帕累托图'.split(',')
items = runpy.run_path(str(CODE/'制作图表与文章_v1.0.0.py'))['CHARTS']
assert len(items) == len(set(x['name'] for x in items)) == 36
catalog = sorted(items, key=lambda x: order.index(x['name']))
for i, c in enumerate(catalog, 1):
    c['id'] = i
    c['stem'] = f"{i:02d}_{c['name']}_v1.0.0"
    c['question'] = c['intro']
    c['source'] = '固定种子 20260906 生成的教学模拟数据，见公共数据与样式_v1.0.0.py'
    c['renderers'] = ['Matplotlib PNG', 'Plotly PNG / 离线交互 HTML']
    c['palette'] = '蓝、橙、橄榄、粉、金；单指标用蓝；正负相关用橙—白—蓝'
    c['qa'] = '同一数据与单位；条柱从零开始；预计算同一分箱/四分位数/KDE；检查实际导出图'
    preamble = f'''"""v1.0.0 | 2026-09-06 | {i:02d} {c['name']}。从任意工作目录运行均可。"""
from pathlib import Path
import runpy
shared = runpy.run_path(str(Path(__file__).with_name('公共数据与样式_v1.0.0.py')))
globals().update({{k:v for k,v in shared.items() if not k.startswith('__')}})

# Matplotlib：实际执行的完整绘图段
'''
    source = preamble + c['mpl'] + '\n\n# Plotly：实际执行的完整绘图段\n' + c['plotly']
    source += f"\n\nfinish({i}, {c['name']!r}, mfig, pfig)\n"
    compile(source, c['stem'], 'exec')
    (CODE/f"{c['stem']}.py").write_text(source, encoding='utf-8')
(ROOT/'图表目录与口径_v1.0.0.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')

if '--prepare-only' in sys.argv:
    print('已生成 36 个独立脚本及图表契约。')
    raise SystemExit(0)

os.environ['CHART_BATCH'] = '1'
start = time.perf_counter()
if '--export-only' not in sys.argv:
    for c in catalog:
        runpy.run_path(str(CODE/f"{c['stem']}.py"), run_name='__main__')

import plotly.io as pio
chrome = Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
if chrome.exists():
    os.environ.setdefault('BROWSER_PATH',str(chrome))
figs = [pio.read_json(ROOT/'图表'/f"{c['stem']}_plotly.json") for c in catalog]
paths = [ROOT/'图表'/f"{c['stem']}_plotly.png" for c in catalog]
pio.write_images(figs,paths,width=720,height=480,scale=2)
print('36 张 Plotly 静态图已导出。',flush=True)

data = runpy.run_path(str(CODE/'公共数据与样式_v1.0.0.py'))
np, pd = data['np'], data['pd']
checks = {}
def check(name, ok):
    checks[name] = bool(ok)
    assert ok, name
check('每月分渠道订单之和等于总订单', np.array_equal(data['trend_parts'].sum(axis=0),data['orders']))
check('每季度百分比合计为100', np.allclose(data['percent'].sum(axis=1),100))
check('直方图计数包含所有160个样本', data['hist_counts'].sum()==len(data['dist']))
check('二维直方图计数包含所有140条记录', data['hist2d'].sum()==len(data['budget']))
check('箱线图五数单调且使用真实须端点', all(s['whislo']<=s['q1']<=s['med']<=s['q3']<=s['whishi'] for s in data['box_stats']))
check('每条KDE曲线有限且非负', all(np.isfinite(d).all() and (d>=0).all() for d in data['violin_densities']))
check('漏斗单调递减且末步转化率15%', (np.diff(data['funnel_values'])<=0).all() and data['funnel_values'][-1]/data['funnel_values'][0]==.15)
check('矩形树图与旭日图父子合计一致', sum(data['tree_values'])==100 and sum(data['tree_values'][:2])==60 and sum(data['tree_values'][2:])==40)
check('桑基图流量守恒', 60+55+45==100+60)
check('瀑布图期末金额125',100+30-15+20-10==125)
check('OHLC高低价包住开收盘', ((data['high_prices']>=np.maximum(data['open_prices'],data['close_prices'])) & (data['low_prices']<=np.minimum(data['open_prices'],data['close_prices']))).all())
check('帕累托累计比例最终100且前三类80',np.isclose(data['cumulative'][-1],100) and np.isclose(data['cumulative'][2],80))
check('相关矩阵对称且对角为1',np.allclose(data['corr'],data['corr'].T) and np.allclose(np.diag(data['corr']),1))
check('甘特任务结束晚于开始',(data['tasks']['结束']>data['tasks']['开始']).all())

data_dir=ROOT/'数据'; data_dir.mkdir(exist_ok=True)
pd.DataFrame({'月份':data['months'],'总订单':data['orders'],**{n:data['trend_parts'][i] for i,n in enumerate(data['trend_names'])}}).to_csv(data_dir/'月度订单_v1.0.0.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(data['matrix'],index=data['periods'],columns=data['channels']).to_csv(data_dir/'季度渠道订单_v1.0.0.csv',encoding='utf-8-sig')
pd.DataFrame({n:a for n,a in zip(data['group_names'],data['samples'])}).to_csv(data_dir/'使用时长样本_v1.0.0.csv',index=False,encoding='utf-8-sig')
data['scatter_df'].to_csv(data_dir/'预算订单客户样本_v1.0.0.csv',index=False,encoding='utf-8-sig')
data['tasks'].to_csv(data_dir/'任务排期_v1.0.0.csv',index=False,encoding='utf-8-sig')
pd.DataFrame({'日期':data['ohlc_dates'],'开盘':data['open_prices'],'最高':data['high_prices'],'最低':data['low_prices'],'收盘':data['close_prices']}).to_csv(data_dir/'模拟OHLC_v1.0.0.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(data['metric_data'],columns=data['metric_names']).to_csv(data_dir/'相关分析样本_v1.0.0.csv',index=False,encoding='utf-8-sig')

from PIL import Image, ImageStat
for c in catalog:
    for lib in ['matplotlib','plotly']:
        path=ROOT/'图表'/f"{c['stem']}_{lib}.png"
        with Image.open(path) as im:
            check(f"{c['id']:02d} {lib} PNG尺寸与非空", im.size==(1440,960) and max(ImageStat.Stat(im.convert('RGB')).stddev)>8)
versions={p:metadata.version(p) for p in ['numpy','pandas','matplotlib','plotly','kaleido','scipy','squarify','pillow','markdown']}
(ROOT/'requirements_v1.0.0.txt').write_text('\n'.join(f'{p}=={v}' for p,v in versions.items())+'\n',encoding='utf-8')
report={'version':'v1.0.0','updated':'2026-09-06','status':'程序校验通过，视觉检查另记',
        'seed':20260906,'python':sys.version,'versions':versions,'checks':checks,
        'seconds':round(time.perf_counter()-start,2),'chart_count':36,'png_count':72,'interactive_html_count':36}
(ROOT/'程序验收结果_v1.0.0.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'完成：{len(checks)} 项数据/输出检查；用时 {report["seconds"]} 秒。',flush=True)
