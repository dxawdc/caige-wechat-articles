"""S44 排位分析 v1.2.0 | 2026-09-14 | 只读源数据、输出衍生分析。
用法：python 分析_v1.2.0.py --input 战绩明细_v1.1.0.csv --mapping 段位映射证据_v1.1.0.json
"""
from pathlib import Path
import argparse, json, hashlib, platform
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent

def records(frame):
    return json.loads(frame.to_json(orient='records', force_ascii=False, date_format='iso'))

def summarize(g):
    return pd.Series({'场次':len(g), '胜场':int(g.win.sum()), '负场':int((~g.win).sum()),
        '胜率':g.win.mean(), '胜方MVP次数':int(g.win_mvp.sum()),'败方MVP次数':int(g.lose_mvp.sum()),
        'MVP次数':int(g.mvp.sum()), 'MVP率':g.mvp.mean(),
        '获胜局MVP率':g.win_mvp.sum()/g.win.sum() if g.win.sum() else np.nan,
        '场均击杀':g['击杀'].mean(), '场均死亡':g['死亡'].mean(), '场均助攻':g['助攻'].mean(),
        '场均评分':g['评分'].mean(), '场均时长分钟':g.minutes.mean(),
        '金牌次数':int(g.gold.sum()), '银牌次数':int(g.silver.sum())})

def group(d, col):
    return pd.DataFrame([dict(zip([col],[k]), **summarize(g).to_dict()) for k,g in d.groupby(col, dropna=False)])

def runs(d):
    rid=d.win.ne(d.win.shift()).cumsum()
    out=[]
    for _,g in d.groupby(rid):
        out.append({'类型':'连胜' if g.win.iloc[0] else '连败','场次':len(g),
                    '开始':str(g.start.iloc[0]),'结束':str(g.end.iloc[-1]),
                    '首局序号':int(g.seq.iloc[0]),'末局序号':int(g.seq.iloc[-1])})
    return pd.DataFrame(out)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--mapping', type=Path, required=True)
    p.add_argument('--output',type=Path,default=ROOT)
    args=p.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    tables=out/'统计表_v1.2.0';tables.mkdir(exist_ok=True)
    source=pd.read_csv(args.input)
    source['start']=pd.to_datetime(source['开局时间']).dt.tz_localize('Asia/Shanghai')
    source['end']=pd.to_datetime(source['结束时间']).dt.tz_localize('Asia/Shanghai')
    boundary=pd.Timestamp('2026-07-01',tz='Asia/Shanghai')
    d=source.loc[(source['模式']=='排位赛')&(source.start>=boundary)].sort_values('end').copy().reset_index(drop=True)
    assert len(d)>0 and d['对局唯一键'].is_unique
    required=['组队人数','胜方MVP原值','败方MVP原值','时长秒','击杀','死亡','助攻','段位编码_列表','星数_列表','评分']
    assert not d[required].isna().any().any()
    assert set(d['结果'])<={'胜利','失败'} and set(d['组队人数'])<={1,2,3,5}
    d['seq']=np.arange(1,len(d)+1);d['win']=d['结果'].eq('胜利')
    d['win_mvp']=d['胜方MVP原值'].eq(1)&d.win
    d['lose_mvp']=d['败方MVP原值'].eq(1)&~d.win
    d['mvp']=d.win_mvp|d.lose_mvp
    assert not ((d['胜方MVP原值']==1)&~d.win).any()
    assert not ((d['败方MVP原值']==1)&d.win).any()
    d['minutes']=d['时长秒']/60
    d['date']=d.start.dt.strftime('%Y-%m-%d')
    d['settle_date']=d.end.dt.strftime('%Y-%m-%d')
    d['weekday']=d.start.dt.dayofweek;d['hour']=d.start.dt.hour
    d['gold']=d['牌子'].fillna('').str.startswith('金牌')
    d['silver']=d['牌子'].fillna('').str.startswith('银牌')
    mapping=json.loads(args.mapping.read_text(encoding='utf-8'))['mapping']
    d['rank_score']=[mapping[str(int(c))]['previousStars']+int(s) for c,s in zip(d['段位编码_列表'],d['星数_列表'])]
    # 统一刻度是可视化坐标，不是官方积分。初始由用户明确确认：钻石 IV 1 星。
    d['rank_delta']=d.rank_score.diff()
    initial_rank_score=mapping['21']['previousStars']+1
    d.loc[0,'rank_delta']=d.loc[0,'rank_score']-initial_rank_score
    d['rank_up']=d.rank_delta.clip(lower=0)
    d['rank_down']=-d.rank_delta.clip(upper=0)
    d['cumulative_net']=d.rank_score-initial_rank_score
    d['cumulative_up']=d.rank_up.cumsum();d['cumulative_down']=d.rank_down.cumsum()
    d['rolling20']=d.win.rolling(20,min_periods=20).mean()
    d['daily_kills']=d.groupby('date')['击杀'].transform('mean')
    d['session_id']=(d.start-d.end.shift()).gt(pd.Timedelta(minutes=60)).fillna(True).cumsum()
    teams=group(d,'组队人数');heroes=group(d,'英雄').sort_values('场次',ascending=False)
    weekdays=group(d,'weekday').set_index('weekday').reindex(range(7)).reset_index()
    hours=group(d,'hour').set_index('hour').reindex(range(24)).reset_index()
    for f in (weekdays,hours):
        for col in ['场次','胜场','负场','胜方MVP次数']:f[col]=f[col].fillna(0).astype(int)
    # 以首个观测日至截止日计算星期暴露次数；9/14 零排位，但仍属于观察窗口。
    calendar=pd.date_range(d.start.min().normalize(),source.end.max().normalize(),freq='D')
    exposure=pd.Series(calendar.dayofweek).value_counts()
    weekdays['观察天数']=weekdays.weekday.map(exposure)
    weekdays['每个日历日平均场次']=weekdays['场次']/weekdays['观察天数']
    heat=pd.crosstab(d.weekday,d.hour).reindex(index=range(7),columns=range(24),fill_value=0)
    daily=group(d,'date').sort_values('date')
    daily['总时长小时']=daily['场次']*daily['场均时长分钟']/60
    rankdaily=d.groupby('settle_date').agg(场次=('seq','size'),有效变化场次=('rank_delta','count'),
        净升星=('rank_delta',lambda x:x.sum(min_count=1)),首局赛后刻度=('rank_score','first'),
        末局赛后刻度=('rank_score','last'),胜场=('win','sum')).reset_index()
    rankdaily['完整日变化']=rankdaily['场次'].eq(rankdaily['有效变化场次'])
    movement=d.groupby('settle_date').agg(累计升星=('rank_up','sum'),累计掉星=('rank_down','sum'),
        掉星场次=('rank_delta',lambda x:int((x<0).sum())),末局段位=('历史段位含星','last')).reset_index()
    rankdaily=rankdaily.merge(movement,on='settle_date',validate='one_to_one')
    rankdaily['日初刻度']=rankdaily['末局赛后刻度']-rankdaily['净升星']
    eligible=rankdaily[rankdaily['完整日变化']]
    best=eligible[eligible['净升星']==eligible['净升星'].max()]
    worst=eligible[eligible['净升星']==eligible['净升星'].min()]
    milestones=[]
    for label, threshold in [('首次王者',100),('首次荣耀王者',150)]:
        # 星耀 I 满 5 星与王者 0 星可能共享刻度；晋级必须核对段位编码类别。
        g=d[d['段位大类'].eq('王者') & (d['星数_列表'] >= (50 if threshold==150 else 0))]
        if len(g):
            r=g.iloc[0];before=d[d.seq<=r.seq]
            milestones.append({'里程碑':label,'序号':int(r.seq),'结束时间':str(r.end),'日期':r.settle_date,
                '段位':r['历史段位含星'],'英雄':r['英雄'],'结果':r['结果'],'累计胜场':int(before.win.sum()),
                '累计胜率':before.win.mean(),'刻度':int(r.rank_score)})
    duration_edges=[0,10,15,20,25,30,np.inf]
    duration_labels=['<10','10–15','15–20','20–25','25–30','≥30']
    d['duration_bin']=pd.cut(d.minutes,duration_edges,labels=duration_labels,right=False)
    duration=group(d,'duration_bin').set_index('duration_bin').reindex(duration_labels).reset_index()
    kills=d.groupby('击杀').size().reindex(range(int(d['击杀'].max())+1),fill_value=0).rename('场次').reset_index()
    dk=daily['场均击杀'];edges=[0,2,4,6,8,np.inf];labels=['<2','2–4','4–6','6–8','≥8']
    dailykill=pd.cut(dk,edges,labels=labels,right=False).value_counts(sort=False).rename('天数').rename_axis('日均击杀区间').reset_index()
    tags=group(d.assign(对局评价=d['对局评价'].fillna('未标注')),'对局评价').sort_values('场次',ascending=False)
    medals=d[d.gold|d.silver].copy()
    medals['牌子等级']=medals['牌子'].str[:2];medals['牌子分路']=medals['牌子'].str[2:]
    medal_lanes=pd.crosstab(medals['牌子分路'],medals['牌子等级']).reindex(
        index=['中路','发育路','游走','上路','打野'],columns=['金牌','银牌'],fill_value=0).reset_index()
    medal_heroes=pd.crosstab(medals['英雄'],medals['牌子等级']).reindex(columns=['金牌','银牌'],fill_value=0)
    medal_heroes['合计']=medal_heroes.sum(axis=1);medal_heroes=medal_heroes.sort_values(['合计','金牌'],ascending=False).reset_index()
    detail_sample=d[d['详情状态'].eq('已采集')].copy()
    def detail_badge(row):
        if pd.isna(row.get('分路牌子编码_详情')):return '编码缺失'
        code=int(row['分路牌子编码_详情'])
        return '未获牌' if code==0 else '顶级' if 1<=code<=5 else '金牌' if 6<=code<=10 else '银牌' if 11<=code<=15 else '铜牌' if 16<=code<=20 else '未知编码'
    detail_badge_counts=detail_sample.apply(detail_badge,axis=1).value_counts().reindex(['顶级','金牌','银牌','铜牌','未获牌','编码缺失','未知编码'],fill_value=0).rename('场次').rename_axis('牌子等级').reset_index()
    rating=d['评分']
    rating_edges=np.arange(np.floor(rating.min()/2)*2,np.floor(rating.max()/2)*2+3,2)
    rating_bins=pd.cut(rating,rating_edges,right=False)
    rating_distribution=d.assign(评分区间=rating_bins).groupby('评分区间',observed=False).agg(
        场次=('seq','size'),胜场=('win','sum')).reset_index()
    rating_distribution['负场']=rating_distribution['场次']-rating_distribution['胜场']
    rating_distribution['占比']=rating_distribution['场次']/len(d)
    rating_distribution['下界']=rating_distribution['评分区间'].apply(lambda x:float(x.left)).astype(float)
    rating_distribution['上界']=rating_distribution['评分区间'].apply(lambda x:float(x.right)).astype(float)
    rating_distribution['评分区间']=rating_distribution['评分区间'].astype(str)
    extrema_fields=['seq','开局时间','英雄','评分','结果','击杀','死亡','助攻','对局评价']
    rating_extrema=pd.concat([d.loc[rating.eq(rating.min()),extrema_fields].assign(纪录='最低评分'),
        d.loc[rating.eq(rating.max()),extrema_fields].assign(纪录='最高评分')],ignore_index=True)
    rating_extrema.to_csv(out/'评分极值对局_私有_v1.2.0.csv',index=False,encoding='utf-8-sig')
    rating_summary={'count':int(rating.count()),'mean':float(rating.mean()),'median':float(rating.median()),
        'q1':float(rating.quantile(.25)),'q3':float(rating.quantile(.75)),
        'min':float(rating.min()),'max':float(rating.max()),
        'at_least_10':int(rating.ge(10).sum()),'below_6':int(rating.lt(6).sum()),
        'win_mean':float(rating[d.win].mean()),'loss_mean':float(rating[~d.win].mean()),
        'extrema':records(rating_extrema)}
    assert rating_bins.notna().all() and rating_distribution['场次'].sum()==len(d)
    run=runs(d)
    # 只用下一局之前的信息选择触发点，不能按事后已结束的连胜段筛选。
    run_id=d.win.ne(d.win.shift()).cumsum()
    run_length=d.groupby(run_id).cumcount()+1
    previous_length=run_length.shift();previous_win=d.win.shift()
    last_three=d.win.astype(int).rolling(3).sum().shift()
    streak_rows=[];streak_events=[]
    for method in ['首次达到3场','滚动最近3场']:
        for condition,value in [('3连胜',True),('3连败',False)]:
            mask=(previous_length.eq(3)&previous_win.eq(value)) if method=='首次达到3场' else last_three.eq(3 if value else 0)
            sample=d[mask];n=len(sample);wins=int(sample.win.sum());rate=wins/n if n else None
            if n:
                z=1.96;den=1+z*z/n;center=(rate+z*z/(2*n))/den
                radius=z*((rate*(1-rate)/n+z*z/(4*n*n))**.5)/den
                lo,hi=center-radius,center+radius
            else:lo=hi=None
            streak_rows.append({'口径':method,'触发条件':condition,'下一局场次':n,'下一局胜场':wins,
                '下一局负场':n-wins,'下一局胜率':rate,'Wilson95下界':lo,'Wilson95上界':hi})
            for _,row in sample.iterrows():streak_events.append({'口径':method,'触发条件':condition,
                '下一局序号':int(row.seq),'下一局开局时间':str(row.start),'下一局结果':row['结果'],
                '前一局连续场数':int(previous_length.loc[row.name])})
    streak_table=pd.DataFrame(streak_rows)
    pd.DataFrame(streak_events).to_csv(out/'三连后下一局事件_私有_v1.2.0.csv',index=False,encoding='utf-8-sig')
    stage=group(d,'历史段位').sort_values('场次',ascending=False)
    teamstage=pd.crosstab(d['组队人数'],d['段位大类']).reset_index()
    sessions=d.groupby('session_id').agg(场次=('seq','size'),胜场=('win','sum'),开始=('start','first'),结束=('end','last')).reset_index()
    # 相邻排位中连续胜负，不声称中途没有巅峰赛或长时间休息。
    winrun=run[run['类型']=='连胜'];lossrun=run[run['类型']=='连败']
    crossday=d[d.date!=d.settle_date]
    summary={'version':'v1.2.0','season':'S44（2026-07-01 起，用户确认）',
        'source_sha256':hashlib.sha256(args.input.read_bytes()).hexdigest(),
        'python':platform.python_version(),'pandas':pd.__version__,
        'source_rows':len(source),'matches':len(d),'wins':int(d.win.sum()),'losses':int((~d.win).sum()),
        'win_rate':d.win.mean(),'win_mvp':int(d.win_mvp.sum()),'win_mvp_rate':d.win_mvp.mean(),
        'lose_mvp':int(d.lose_mvp.sum()),'mvp_total':int(d.mvp.sum()),'mvp_rate':d.mvp.mean(),
        'win_conditional_mvp_rate':d.win_mvp.sum()/d.win.sum(),
        'first_start':str(d.start.min()),'last_start':str(d.start.max()),'last_end':str(d.end.max()),
        'snapshot_end':str(source.end.max()),'active_days':int(d.date.nunique()),'observed_days':len(calendar),
        'heroes':int(d['英雄'].nunique()),'play_hours':d.minutes.sum()/60,
        'mean_minutes':d.minutes.mean(),'median_minutes':d.minutes.median(),
        'min_minutes':d.minutes.min(),'max_minutes':d.minutes.max(),'p90_minutes':d.minutes.quantile(.9),
        'kills_mean':d['击杀'].mean(),'kills_median':d['击杀'].median(),'kills_max':int(d['击杀'].max()),
        'deaths_mean':d['死亡'].mean(),'assists_mean':d['助攻'].mean(),
        'detail_available':int(d['详情状态'].eq('已采集').sum()),'detail_missing':int(d['详情状态'].ne('已采集').sum()),
        'first_rank':d['历史段位含星'].iloc[0],'last_rank':d['历史段位含星'].iloc[-1],
        'initial_rank':'永恒钻石IV 1星（用户确认的首局赛前基线）','initial_rank_score':initial_rank_score,
        'observed_net_rank_change':int(d.rank_score.iloc[-1]-initial_rank_score),
        'gross_rank_up':int(d.rank_up.sum()),'gross_rank_down':int(d.rank_down.sum()),
        'daily_positive_net_sum':int(rankdaily['净升星'].clip(lower=0).sum()),
        'daily_negative_net_sum':int(-rankdaily['净升星'].clip(upper=0).sum()),
        'positive_net_days':int((rankdaily['净升星']>0).sum()),'zero_net_days':int(rankdaily['净升星'].eq(0).sum()),
        'negative_net_days':int((rankdaily['净升星']<0).sum()),'days_with_any_drop':int((rankdaily['累计掉星']>0).sum()),
        'negative_net_dates':records(rankdaily[rankdaily['净升星']<0]),
        'movement_distribution':{str(int(k)):int(v) for k,v in d.rank_delta.value_counts().sort_index().items()},
        'extra_above_one_on_win':int((d.loc[d.win,'rank_delta']-1).sum()),
        'rank_peak':int(d.rank_score.max()),'rank_peak_rows':records(d.loc[d.rank_score==d.rank_score.max(),['seq','结束时间','历史段位含星']]),
        'milestones':milestones,'best_days':records(best),'worst_days':records(worst),
        'max_win_runs':records(winrun[winrun['场次']==winrun['场次'].max()]),
        'max_loss_runs':records(lossrun[lossrun['场次']==lossrun['场次'].max()]),
        'gold':int(d.gold.sum()),'silver':int(d.silver.sum()),
        'cross_midnight_matches':len(crossday),'zero_deaths':int(d['死亡'].eq(0).sum()),
        'zero_kills':int(d['击杀'].eq(0).sum()),'zero_kills_wins':int(d.loc[d['击杀'].eq(0),'win'].sum()),
        'negative_delta_on_win':int((d.win&(d.rank_delta<0)).sum()),
        'loss_no_delta':int((~d.win&d.rank_delta.eq(0)).sum()),
        'loss_positive_delta':int((~d.win&(d.rank_delta>0)).sum()),
        'loss_positive_records':records(d.loc[~d.win&(d.rank_delta>0),['seq','结束时间','历史段位含星','英雄','rank_delta']]),
        'zero_death_wins':int(d.loc[d['死亡'].eq(0),'win'].sum()),
        'after_loss_win_rate':float(d.loc[d.win.shift().eq(False),'win'].mean()),
        'after_loss_n':int(d.win.shift().eq(False).sum()),
        'after_win_win_rate':float(d.loc[d.win.shift().eq(True),'win'].mean()),
        'after_win_n':int(d.win.shift().eq(True).sum()),
        'max_kill_record':records(d.loc[d['击杀']==d['击杀'].max(),['开局时间','英雄','击杀','死亡','助攻','结果']]),
        'top_active_dates':records(daily.nlargest(3,'场次')),
        'medal_total':int(d.gold.sum()+d.silver.sum()),'medal_rate':float((d.gold|d.silver).mean()),
        'detail_badge_counts':records(detail_badge_counts),
        'medal_lane_counts':records(medal_lanes),'medal_hero_counts':records(medal_heroes),
        'streak3_next_match':records(streak_table),'rating':rating_summary}
    frames={'组队':teams,'英雄':heroes,'星期':weekdays,'小时':hours,'日期':daily,'每日升降星':rankdaily,
        '时长分布':duration,'单局击杀分布':kills,'每日场均击杀分布':dailykill,'局评价':tags,
        '连续胜负':run,'段位分布':stage,'组队段位构成':teamstage,'会话':sessions,
        '金银牌分路':medal_lanes,'金银牌英雄':medal_heroes,'完整详情牌子分布':detail_badge_counts,
        '三连后下一局胜率':streak_table,'对局评分分布':rating_distribution}
    for name,f in frames.items():f.to_csv(tables/f'{name}_v1.2.0.csv',index=False,encoding='utf-8-sig')
    heat.to_csv(tables/'星期小时矩阵_v1.2.0.csv',encoding='utf-8-sig')
    d.to_csv(out/'S44排位分析明细_私有_v1.2.0.csv',index=False,encoding='utf-8-sig')
    # 无角色、选手、对局ID；可视化所需的逐局轨迹保留本地，不随公开资料发布。
    payload={'summary':summary,'tables':{k:records(v) for k,v in frames.items()},'heatmap':heat.values.tolist(),
        'trajectory':records(d[['seq','date','settle_date','rank_score','rank_delta','cumulative_net','cumulative_up','cumulative_down','历史段位含星','win','rolling20']])}
    (out/'分析结果_私有_v1.2.0.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    (out/'统计摘要_v1.2.0.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    assert sum(teams['场次'])==len(d)==int(heat.to_numpy().sum())==int(kills['场次'].sum())
    assert sum(teams['胜场'])==int(d.win.sum()) and sum(heroes['MVP次数'])==int(d.mvp.sum())
    assert int(d.rank_delta.dropna().sum())==summary['observed_net_rank_change']
    assert duration['场次'].sum()==len(d) and dailykill['天数'].sum()==summary['active_days']
    (out/'口径验收_v1.2.0.json').write_text(json.dumps({'status':'passed','rows':len(d),'unique':True,
        'key_fields_complete':True,'group_totals_reconciled':True,'rank_delta_reconciled':True,
        'first_rank_delta':int(d.rank_delta.iloc[0]),'initial_source':'用户确认钻石IV 1星',
        'balance_equation':f'{initial_rank_score}+{int(d.rank_up.sum())}-{int(d.rank_down.sum())}={int(d.rank_score.iloc[-1])}',
        'daily_net_reconciled':bool(rankdaily['净升星'].sum()==d.rank_delta.sum()),
        'cross_midnight':records(crossday[['开局时间','结束时间']])},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
