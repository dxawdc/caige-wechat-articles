"""v1.0.0 | Executable article snippets, in reading order; input is a local snapshot."""
# BEGIN LOAD_DATA
from pathlib import Path
import sys
import pandas as pd

DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    'private/clean_v1.0.0/reviews_private_v1.0.0.csv')
d = pd.read_csv(DATA, dtype={'review_id': str})
for col in ['created_time', 'edited_time', 'version_time']:
    d[col] = pd.to_datetime(d[col], utc=True).dt.tz_convert('Asia/Shanghai')
d['positive'] = d.score.between(4, 5)
d['negative'] = d.score.between(1, 2)
launch = pd.Timestamp('2026-09-10 07:00:00', tz='Asia/Shanghai')
# END LOAD_DATA

# BEGIN RATING_CODE
rating_counts = d.score.value_counts().sort_index()
rating_share = rating_counts / len(d)
print(pd.DataFrame({'条数': rating_counts, '占比': rating_share}))
# END RATING_CODE

# BEGIN WINDOW_CODE
from analyze_v1_0_0 import summarize

pre = d[(d.version_time >= launch - pd.Timedelta(days=4))
        & (d.version_time < launch)]
post = d[(d.version_time >= launch)
         & (d.version_time < launch + pd.Timedelta(days=4))]
print('首发前96小时', summarize(pre))
print('首发后96小时', summarize(post))
# END WINDOW_CODE

# BEGIN HOURS_CODE
d['played_hours'] = d.played_seconds / 3600
d['play_group'] = pd.cut(
    d.played_hours, [-0.001, 1, 5, 20, float('inf')], right=False,
    labels=['不足1小时', '1–5小时', '5–20小时', '20小时及以上']
).astype('string').fillna('未展示评价时长')
print(d.groupby('play_group').positive.agg(['size', 'mean']))
# END HOURS_CODE

# BEGIN THEME_CODE
from analyze_v1_0_0 import THEMES

for theme, pattern in THEMES.items():
    d[theme] = d.text.fillna('').str.contains(pattern, regex=True, case=False)
theme_count = d[list(THEMES)].sum().sort_values(ascending=False)
theme_share = theme_count / len(d)
print(pd.DataFrame({'提及数': theme_count, '提及占比': theme_share}))
# END THEME_CODE

# BEGIN EVOLUTION_CODE
from analyze_v1_0_0 import PERIODS

# period已在prepare脚本中按开服时刻和版本时间生成
near_launch = d[d.period.isin(PERIODS)]
theme_evolution = near_launch.groupby('period')[list(THEMES)].mean()
theme_evolution = theme_evolution.reindex(PERIODS)
phase_size = near_launch.groupby('period').size().reindex(PERIODS)
print(phase_size)
print(theme_evolution)
# END EVOLUTION_CODE

# BEGIN TFIDF_CODE
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from analyze_v1_0_0 import tokenize

corpus = d[~d.text.duplicated() & d.period.isin(PERIODS)].copy()
docs = corpus.text.map(lambda text: ' '.join(tokenize(text)))
vectorizer = TfidfVectorizer(
    tokenizer=str.split, token_pattern=None, lowercase=False,
    min_df=5, max_df=0.8, max_features=4000, sublinear_tf=True)
X = vectorizer.fit_transform(docs)
words = vectorizer.get_feature_names_out()
nonzero = np.asarray(X.sum(axis=1)).ravel() > 0
for period in PERIODS:
    mask = corpus.period.eq(period).to_numpy() & nonzero
    weights = np.asarray(X[mask].mean(axis=0)).ravel()
    top = weights.argsort()[-10:][::-1]
    print(period, words[top].tolist())
# END TFIDF_CODE

# BEGIN NMF_CODE
from sklearn.decomposition import NMF

model = NMF(n_components=6, init='nndsvda', random_state=42, max_iter=800)
W = model.fit_transform(X[nonzero])
topic_id = W.argmax(axis=1)
for i, component in enumerate(model.components_):
    top = component.argsort()[-8:][::-1]
    print(i + 1, int((topic_id == i).sum()), words[top].tolist())
# END NMF_CODE

assert len(d) == d.review_id.nunique()
assert len(pre) + len(post) <= len(d)
print('Article walkthrough executed.')
