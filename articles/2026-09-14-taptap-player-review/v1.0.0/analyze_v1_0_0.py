"""v1.0.0 | Rating-based opinion signals + explicit multi-label themes + TF-IDF/NMF.
Input is the private normalized CSV. Public outputs contain aggregates only.
"""
import argparse
import json
import re
import shutil
from pathlib import Path
import jieba
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF

LAUNCH = pd.Timestamp('2026-09-10 07:00:00', tz='Asia/Shanghai')
PERIODS = ['首发前7天','首发首24小时','首发第2–4天','第5天未完整']
# Mention detection, not aspect sentiment. One review may match multiple themes.
THEMES = {
 '玩法与策略': r'玩法|策略|博弈|羁绊|利息|阵容|拍卖|合成|买三卖一|买3卖1|流派|转型|天赋',
 '平衡与随机': r'平衡|运气|随机|数值|超模|强度|天胡|发牌|轮椅|削弱|强势|概率',
 '福利与任务': r'点券|点卷|任务|福利|奖励|领皮肤|送皮肤|肝度|联动(?:活动|福利|任务)',
 '美术与音画': r'画面|画风|建模|美术|特效|音效|立绘|配音|画质|[Qq]版',
 '新手与引导': r'新手|教程|引导|上手|教学|入门|糖宝|灵宝|[Aa][Ii].{0,3}(?:指导|助手)',
 '性能与适配': r'卡顿|闪退|发热|掉帧|黑屏|崩溃|适配|帧率|卡屏|延迟|耗电|(?:画面|屏幕|界面|游戏|手机).{0,5}卡死|(?:性能|画质|手机).{0,8}优化|优化.{0,8}(?:好|差|不错|不行|手机|流畅|稳定)',
 '安装与登录': r'下载|安装|登录|登陆|进不去|更新包|服务器|排队|加载',
 '节奏与耗时': r'节奏|耗时|坐牢|太拖|太慢|拖沓|半小时|[二三四五六十\d]+分钟|(?:一局|每局).{0,12}(?:时间|太久)',
 '商业化付费': r'氪金|充值|付费|氪佬|首充|首冲|战令|氪度',
 '同类游戏对照': r'炉石|酒馆|云顶|金铲铲|铲铲|月圆之夜|多多自走棋|模拟战|因缘精灵',
}
STOP = set('的 了 和 是 我 你 他 她 它 也 就 都 很 还 有 在 这 那 啊 吧 呢 一下 一个 这个 那个 这种 那种 但是 就是 还是 不是 没有 可以 感觉 觉得 真的 什么 怎么 现在 游戏 玩 玩过 好玩 不好玩 王者 万象 万象棋 王者万象棋 自走棋 玩家 游戏体验 表情 期待 不错 不知道 时候 一样 所以 然后 以及 比较 已经 自己 不能 不如 多少 一直 一点 总体 个人 其实 可能 有点 东西 起来 而且 的话 来说 只能 这么 那么 这样 那样 反正 确实 直接 非常 完全'.split())
for term in ['金铲铲','铲铲','月圆之夜','酒馆战棋','万象棋','点券','点卷','孙尚香','灵宝','自走棋','买三卖一']:
    jieba.add_word(term)
STOP.update('还有 实在 为了 不了 不用 怎么样 什么样 觉得挺 因为 虽然 不过 一个个 至少 毕竟 总之 基本 特别 有些 发现 也是 只是 甚至 毫无 只有 真的很'.split())

def tokenize(text):
    text=re.sub(r'\[表情_[^\]]+\]|https?://\S+', ' ', str(text))
    return [w.lower() for w in jieba.lcut(text) if len(w)>1 and w not in STOP
            and re.fullmatch(r'[\u4e00-\u9fffA-Za-z]+',w)]

def wilson(k,n,z=1.96):
    if not n:return [None,None]
    p=k/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den
    radius=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [float(center-radius),float(center+radius)]

def summarize(g):
    s=g[g.score.between(1,5)];n=len(s);pos=int(s.positive.sum());neg=int(s.negative.sum())
    return {'n':n,'high':pos,'middle':int(s.score.eq(3).sum()),'low':neg,
            'high_rate':pos/n if n else None,'low_rate':neg/n if n else None,
            'mean_stars':float(s.score.mean()) if n else None,
            'high_ci':wilson(pos,n),'low_ci':wilson(neg,n)}

def analyze(input_path, output, private_output):
    output.mkdir(parents=True, exist_ok=True);private_output.mkdir(parents=True,exist_ok=True)
    summary_path=input_path.parent/'collection_summary_v1.0.0.json'
    if not summary_path.exists():
        raise FileNotFoundError('Run prepare first: collection summary is required')
    shutil.copy2(summary_path,output/'collection_summary_v1.0.0.json')
    d=pd.read_csv(input_path, dtype={'review_id':str,'user_key':str})
    for key in ['created_time','edited_time','version_time']:
        d[key]=pd.to_datetime(d[key], utc=True).dt.tz_convert('Asia/Shanghai')
    d['text']=d.text.fillna('');d['positive']=d.score.between(4,5);d['negative']=d.score.between(1,2)
    for theme,pattern in THEMES.items():d[theme]=d.text.str.contains(pattern, regex=True,case=False)
    result={'overall':summarize(d),'rating_counts':d.score.value_counts().sort_index().to_dict(),
            'stages':{str(k):summarize(g) for k,g in d.groupby('stage_label')},
            'hours':{str(k):summarize(g) for k,g in d.groupby('play_group')},
            'periods':{p:summarize(d[d.period.eq(p)]) for p in PERIODS},
            'daily':{str(k):summarize(g) for k,g in d.groupby('version_day')},
            'themes':{},'theme_periods':{},'matched':{},'sensitivity':{}}
    for theme in THEMES:
        g=d[d[theme]];result['themes'][theme]={**summarize(g),'mentions':len(g),'mention_rate':len(g)/len(d)}
        result['theme_periods'][theme]={p:{'n':int(d.period.eq(p).sum()),
            'mentions':int((d.period.eq(p)&d[theme]).sum()),
            'rate':float(d.loc[d.period.eq(p),theme].mean())} for p in PERIODS}
    for label,start,end in [('首发前96小时',LAUNCH-pd.Timedelta(days=4),LAUNCH),
                             ('首发后96小时',LAUNCH,LAUNCH+pd.Timedelta(days=4))]:
        m=d.version_time.ge(start)&d.version_time.lt(end)
        result['matched'][label]=summarize(d[m])
        result['matched'][label]['played_only']=summarize(d[m&d.stage_label.eq('玩过')])
        result['matched'][label]['stages']=d.loc[m,'stage_label'].value_counts().to_dict()
    for timecol in ['created_time','version_time']:
        result['sensitivity'][timecol]={}
        for label,start,end in [('pre',LAUNCH-pd.Timedelta(days=4),LAUNCH),('post',LAUNCH,LAUNCH+pd.Timedelta(days=4))]:
            result['sensitivity'][timecol][label]=summarize(d[d[timecol].ge(start)&d[timecol].lt(end)])
    unique=d.loc[~d.text.duplicated()]
    result['sensitivity']['unique_text']=summarize(unique)
    for label,start,end in [('pre',LAUNCH-pd.Timedelta(days=4),LAUNCH),('post',LAUNCH,LAUNCH+pd.Timedelta(days=4))]:
        result['sensitivity']['unique_text_'+label]=summarize(unique[unique.version_time.ge(start)&unique.version_time.lt(end)])
    result['theme_coverage']=int(d[list(THEMES)].any(axis=1).sum())
    result['stage_by_period']={p:d.loc[d.period.eq(p),'stage_label'].value_counts().to_dict() for p in PERIODS}
    # The fitted vocabulary is shared across periods; repeated text gets one vote here.
    corpus=unique[unique.period.isin(PERIODS)].copy();docs=corpus.text.map(lambda s:' '.join(tokenize(s)))
    vec=TfidfVectorizer(tokenizer=str.split, token_pattern=None,lowercase=False,
                         min_df=5,max_df=.8,max_features=4000,sublinear_tf=True)
    x=vec.fit_transform(docs);words=vec.get_feature_names_out();nonzero=np.asarray(x.sum(axis=1)).ravel()>0
    keys={}
    for p in PERIODS:
        mask=corpus.period.eq(p).to_numpy() & nonzero
        weights=np.asarray(x[mask].mean(axis=0)).ravel() if mask.any() else np.zeros(len(words))
        idx=weights.argsort()[-10:][::-1]
        keys[p]={'n':int(mask.sum()),'terms':[{'term':words[j],'weight':float(weights[j])} for j in idx]}
    result['keywords']=keys
    model=NMF(n_components=6,init='nndsvda',random_state=42,max_iter=800)
    w=model.fit_transform(x[nonzero]);topic=w.argmax(axis=1);valid=corpus.loc[nonzero].copy();valid['topic']=topic
    result['nmf']={'documents':len(valid),'vocabulary':len(words),'iterations':model.n_iter_,
       'scope':'current visible versions from 7 days before launch to snapshot',
       'topics':[{'id':i,'n':int((topic==i).sum()),
          'terms':[str(words[j]) for j in h.argsort()[-8:][::-1]]} for i,h in enumerate(model.components_)],
       'period_counts':{p:{str(k):int(v) for k,v in valid.loc[valid.period.eq(p),'topic'].value_counts().items()} for p in PERIODS}}
    # Local-only evidence for manual contextual review. Never publish whole comments.
    audit=[]
    for theme in THEMES:
        pool=d[d[theme]]
        for _,row in pool.sample(min(5,len(pool)),random_state=42).iterrows():
            audit.append({'theme':theme,'review_id':row.review_id,'score':int(row.score),'text':row.text})
    (private_output/'theme_audit_candidates_v1.0.0.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
    valid[['review_id','topic','text']].to_csv(private_output/'nmf_assignments_private_v1.0.0.csv',index=False,encoding='utf-8-sig')
    d.to_csv(private_output/'features_private_v1.0.0.csv',index=False,encoding='utf-8-sig')
    (output/'analysis_v1.0.0.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
    (output/'theme_dictionary_v1.0.0.json').write_text(json.dumps(THEMES,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:result[k] for k in ['overall','matched','nmf']},ensure_ascii=False,indent=2))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--private-output',type=Path,required=True)
    a=p.parse_args();analyze(a.input,a.output,a.private_output)
