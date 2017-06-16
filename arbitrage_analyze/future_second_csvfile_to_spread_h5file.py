# coding=utf-8

# 一个把期货csv文件转化为h5文件的脚本.
# 把两个期货合约合并,计算价差,并写入h5


import pandas as pd
from datetime import datetime, time, date, timedelta
import re
import bisect
import os
import h5py


# 通过期货合约代码的名称得到期货合约的时间.返回
# 期货交割当月的1号0时0分0秒.
def name2time(name):
    """
    :param name: 包含4位时间YYMM的期货合约名称.
    :return: datetime.datetime类型
    """
    pattern = re.compile(r'[901]\d(0\d|1[012])')
    match = pattern.search(name)
    dtstring = match.group()
    dtstring = '19' + dtstring + '01' if dtstring[0] == '9' else '20' + dtstring + '01'
    return datetime.strptime(dtstring, '%Y%m%d')


# 通过期货合约代码的名称得到期货合约的品种
def name2contract(name):
    name = name.split(os.sep)[-1]
    npos = 0
    for i, c in enumerate(name):
        if c.isdigit():
            npos = i
            break
    return name[:npos]


def parse_df(file1, file2, outputfilepath, groupname, nighttimestart=None):
    df1 = pd.read_csv(file1, header=None, parse_dates=[0])
    df2 = pd.read_csv(file2, header=None, parse_dates=[0])
    print 'reading finished...'

    df1.columns = ["datetime", "close", "volume", "position"]
    df2.columns = ["datetime", "close", "volume", "position"]
    df1.set_index(["datetime"], inplace=True)
    df2.set_index(["datetime"], inplace=True)

    df = pd.merge(df1, df2, left_index=True, right_index=True, suffixes=('_n', '_f'))

    print 'merged...'

    df = df_filter(df, file1, nighttimestart, 7200)

    print 'filtered...'
    df['spread'] = df['close_n'] - df['close_f']

    df2hdf5(df, file1, file2, outputfilepath, groupname)
    print 'written.'


def df2hdf5(df, csvfilepath1, csvfilepath2, outputfilepath, groupname):
    dt = df.index
    dt = dt.map(lambda x: x.strftime('%Y%m%d %H:%M:%S'))  # 17位

    close_near = df.ix[:, 'close_n'].values
    close_far = df.ix[:, 'close_f'].values
    spread = df.ix[:, 'spread'].values
    volume_near = df.ix[:, 'volume_n'].values
    volume_far = df.ix[:, 'volume_f'].values

    datasetname = csvfilepath1.split(os.sep)[-1].split('.')[0] + '-' + csvfilepath2.split(os.sep)[-1].split('.')[0]

    with h5py.File(outputfilepath, 'a') as h5file:
        grp = h5file.get(groupname, None)
        if grp is None:
            grp = h5file.create_group(groupname)
        subgrp = grp.get(datasetname, None)
        if subgrp is None:
            subgrp = grp.create_group(datasetname)
        else:
            return
        subgrp.create_dataset('datetime', dt.shape, 'S17', dt)
        subgrp.create_dataset('close_near', close_near.shape, 'f', close_near)
        subgrp.create_dataset('close_far', close_far.shape, 'f', close_far)
        subgrp.create_dataset('spread', spread.shape, 'f', spread)
        subgrp.create_dataset('volume_near', volume_near.shape, 'i4')
        subgrp.create_dataset('volume_far', volume_far.shape, 'i4')

        subgrp.attrs.create('length', len(df), (1,), 'i4')


def get_active_timespan(df, nearmonthname, nightstart):
    neartime = name2time(nearmonthname)

    # 1\5\9活跃
    if name2contract(nearmonthname) in ('i', 'j', 'jm', 'ru'):
        if neartime.month == 5:
            starttime = datetime(neartime.year - 1, 12, 16)
            endtime = datetime(neartime.year, 4, 15)
        elif neartime.month == 9:
            starttime = datetime(neartime.year, 4, 16)
            endtime = datetime(neartime.year, 8, 15)
        else:
            starttime = datetime(neartime.year - 1, 8, 16)
            endtime = datetime(neartime.year - 1, 12, 15)
    # 1\5\10
    elif name2contract(nearmonthname) in ('rb', 'hc'):
        if neartime.month == 5:
            starttime = datetime(neartime.year - 1, 12, 16)
            endtime = datetime(neartime.year, 4, 15)
        elif neartime.month == 10:
            starttime = datetime(neartime.year, 4, 16)
            endtime = datetime(neartime.year, 9, 15)
        else:
            starttime = datetime(neartime.year - 1, 9, 16)
            endtime = datetime(neartime.year - 1, 12, 15)
    # 3\6\9\12
    elif name2contract(nearmonthname) in ('T', 'TF'):
        if neartime.month == 3:
            starttime = datetime(neartime.year - 1, 12, 1)
            endtime = datetime(neartime.year, 3, 1)
        elif neartime.month == 6:
            starttime = datetime(neartime.year, 3, 1)
            endtime = datetime(neartime.year, 6, 1)
        elif neartime.month == 9:
            starttime = datetime(neartime.year, 6, 1)
            endtime = datetime(neartime.year, 9, 1)
        else:
            starttime = datetime(neartime.year, 9, 1)
            endtime = datetime(neartime.year, 12, 1)
    else:
        raise '品种活跃月份不清楚'

    starttime = get_starttime(df.index, starttime.date(), nightstart)
    endtime = get_endtime(df.index, endtime.date(), nightstart)
    return starttime, endtime


# 寻找给定时间的期货当个交易日开盘时间
def get_starttime(timeseries, tm, nightstart=None):
    """
    :param timeseries: pandas.Series对象．item为datetime.datetime． 
    :param tm: 位于timeseries区间内的datetime.date对象．
    :param nightstart: 若非None，为夜盘开始时间．
    :param nightend: 若非None，为夜盘结束时间．
    :return: tm所在交易日的交易起始时间．datetime
    """
    if nightstart is None:
        left_threshold = datetime(tm.year, tm.month, tm.day)
    else:
        while tm.weekday() in (0, 6, 5):
            tm -= timedelta(days=1)

        left_threshold = datetime(tm.year, tm.month, tm.day,
                                      nightstart.hour, nightstart.minute)

    print left_threshold, len(timeseries), timeseries[-1]

    return timeseries[bisect.bisect_left(timeseries, left_threshold)]


# 寻找给定时间的期货当个交易日收盘时间
def get_endtime(timeseries, tm, nightstart=None):
    if nightstart is None:
        right_threshold = datetime(tm.year, tm.month, tm.day) + timedelta(days=1)
    else:
        while tm.weekday() in (4, 5, 6):
            tm += timedelta(days=1)
        right_threshold = datetime(tm.year, tm.month, tm.day,
                                       nightstart.hour, nightstart.minute) - timedelta(minutes=1)
    return timeseries[bisect.bisect_left(timeseries, right_threshold) - 1]


def df_filter(df, file1, nighttimestart, filter_counter):
    """
    对df进行数据过滤,掐头去尾,并把中间无交易的时间段去掉
    :param df: 
    :param file1: 近期合约文件名
    :param nighttimestart: 夜盘开始时间
    :param filter_counter: 某段数据有超过filter_count个个数的数据无交易的话, 删掉这段数据.
    :return: 处理完后的df
    """

    start, end = get_active_timespan(df, file1, nighttimestart)
    df = df.ix[start: end]
    print start, end
    print 'truncated...'

    pos_l = 0
    poss = []
    length = len(df)
    dfarr = df.values[:, [1, 4]]  # 留下volume_n和volume_f
    while pos_l < length:
        item = dfarr[pos_l]
        if item[0] == 0 and item[1] == 0:
            counter = 0
            for itemj in dfarr[pos_l:]:
                if itemj[0] == 0 and itemj[1] == 0:
                    counter += 1
                else:
                    break

            if counter >= filter_counter:
                if pos_l + counter >= len(df):
                    poss.append((pos_l, None))
                else:
                    poss.append((pos_l, pos_l + counter))

            pos_l += counter
            pos_l -= 1

        pos_l += 1

    print poss

    for item in reversed(poss):
        df.drop(df.index[item[0]: item[1]], inplace=True)

    return df


if __name__ == "__main__":

    h5path = './future_spread_arbitrage2.h5'
    for groupname in ('ru',):

        l = []
        for p, ds, fs in os.walk('E:\\wind_data\\future_kdata\\' + groupname):
            for f in fs:
                fullpath = os.path.join(p, f)
                l.append(fullpath)
        filetp = []
        for idx in xrange(len(l)-1):
            filetp.append((l[idx], l[idx+1]))
        for item in filetp:
            parse_df(item[0], item[1], h5path, groupname, nighttimestart=time(21, 0, 0))
            print item
