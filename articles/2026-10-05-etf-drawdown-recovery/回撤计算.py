"""历史窗口内的最大回撤及互不重叠回撤事件；计时为交易日间隔。"""
import numpy as np
import pandas as pd


def max_drawdown_record(frame):
    frame = frame.sort_values('date').reset_index(drop=True).copy()
    prices = frame['close'].to_numpy(dtype=float)
    if len(prices) < 2 or not np.isfinite(prices).all() or (prices <= 0).any():
        raise ValueError('至少需要两个有效的正数收盘价')
    high = np.maximum.accumulate(prices)
    dd = prices / high - 1
    trough = int(np.argmin(dd))
    if dd[trough] >= 0:
        return {'max_drawdown_pct':0.0, 'status':'窗口内无回撤', 'peak_i':None, 'trough_i':None,
                'recovery_i':None, 'peak_date':None, 'trough_date':None, 'recovery_date':None,
                'decline_days':0, 'recovery_days':None, 'observed_after_trough_days':0, 'underwater_days':0}
    # 相同高点取下跌前最后一个；相同最深低点取第一次。
    peak = int(np.flatnonzero(prices[:trough+1] == high[trough])[-1])
    hits = np.flatnonzero(prices[trough+1:] >= prices[peak])
    recovered = int(trough + 1 + hits[0]) if len(hits) else None
    end = recovered if recovered is not None else len(prices)-1
    def date(i):
        return str(pd.Timestamp(frame.loc[i,'date']).date()) if i is not None else None
    return {'max_drawdown_pct':float(dd[trough]*100), 'status':'已修复' if recovered is not None else '尚未修复',
            'peak_i':peak, 'trough_i':trough, 'recovery_i':recovered,
            'peak_date':date(peak), 'trough_date':date(trough), 'recovery_date':date(recovered),
            'peak_close':float(prices[peak]), 'trough_close':float(prices[trough]),
            'decline_days':trough-peak, 'recovery_days':recovered-trough if recovered is not None else None,
            'observed_after_trough_days':len(prices)-1-trough, 'underwater_days':end-peak,
            'peak_at_window_start':peak==0}


def drawdown_events(frame):
    """从窗口内滚动高点开始，每次首次回到高点结束；尚未结束的事件保留空值。"""
    frame = frame.sort_values('date').reset_index(drop=True)
    prices = frame['close'].to_numpy(dtype=float)
    peak, trough, active = 0, None, False
    events = []
    for i in range(1,len(prices)):
        if not active:
            if prices[i] >= prices[peak]:
                peak = i
            else:
                active, trough = True, i
        else:
            if prices[i] < prices[trough]:
                trough = i
            if prices[i] >= prices[peak]:
                events.append(event_record(frame,peak,trough,i))
                peak, trough, active = i, None, False
    if active:
        events.append(event_record(frame,peak,trough,None))
    return events


def event_record(frame,peak,trough,recovery):
    prices = frame['close'].to_numpy(dtype=float)
    return {'peak_date':str(pd.Timestamp(frame.loc[peak,'date']).date()),
            'trough_date':str(pd.Timestamp(frame.loc[trough,'date']).date()),
            'recovery_date':str(pd.Timestamp(frame.loc[recovery,'date']).date()) if recovery is not None else None,
            'depth_pct':float((prices[trough]/prices[peak]-1)*100),
            'decline_days':trough-peak, 'recovery_days':recovery-trough if recovery is not None else None,
            'observed_after_trough_days':len(prices)-1-trough,
            'underwater_days':(recovery if recovery is not None else len(prices)-1)-peak,
            'status':'已修复' if recovery is not None else '尚未修复', 'peak_at_window_start':peak==0}
