# coding=utf-8

# mt4导出的外汇数据的预处理（20120101--20160930），
# 主要是剔除了周末、非周末的非交易日，线性插值。
from datetime import datetime, timedelta
import dateutil.parser
import pandas as pd
import numpy as np

exclude = ['2012.04.06', '2012.12.25', '2013.01.01', '2013.03.29', '2013.06.10',
           '2013.06.27', '2013.06.28', '2013.12.25', '2014.01.01', '2014.04.18',
           '2014.12.25', '2015.01.01', '2015.04.03', '2015.12.25', '2016.01.01', '2016.03.25']
i = 0
df = pd.read_csv('D:/documents/pythonproject/ecophysics/backtest/xagusd1.csv', header=None, date_parser=dateutil.parser.parse, parse_dates=[[0, 1]])
# for df in dfm:
i += 1
df.columns = ['date_time', 'open', 'high', 'low', 'close', 'volume']

df.set_index('date_time', inplace=True)
df = df.resample('60S').asfreq()[:]
df['date_time'] = df.index
df['day'] = df['date_time'].dt.dayofweek
df = df[np.logical_not(np.logical_or(df['day'] == 5, df['day'] == 6))]
df = df[np.logical_not(np.logical_and(np.logical_and(df['date_time'].dt.dayofweek == 4, df['date_time'].dt.hour == 23), df['date_time'].dt.year <= 2013))]
df = df[np.logical_not(np.logical_and(np.logical_and(df['date_time'].dt.dayofweek == 0, df['date_time'].dt.hour == 0), df['date_time'].dt.year >= 2014))]

df['date_time'] = map(lambda x: x.strftime('%Y.%m.%d'), df['date_time'])

for ex in exclude:
    df = df[df['date_time'] != ex]

df = df.apply(pd.Series.interpolate)

df['date_time'] = map(lambda x: x.strftime('%Y.%m.%d %H:%M:%S'), df.index)
del df['day']
df.set_index('date_time', inplace=True)
df.to_csv('D:/documents/pythonproject/ecophysics/backtest/xagusdnew.csv')


# 看有除了周末还有那些天是没有数据的。
# df1 = df.resample('1D').sum()[:]
# df1['date_time'] = df1.index
# df1['day'] = df1['date_time'].dt.dayofweek
# df1 = df1[np.logical_not(np.logical_or(df1['day'] == 5, df1['day'] == 6))]
# df1 = df1[np.logical_not(df1['open'] > 0.01)]
# print df1