# coding=utf-8

# 分别统计如下一些tick的分布情况:
# 1.入场后成功情况下持仓时间内tick的分布.distribution_1
# 2.入场后成功情况下反向最大tick的分布.distribution_2
# 3.入场后失败情况下最后时刻tick的分布.distribution_3
# 4.入场后失败情况下持仓时间内tick的分布.distribution_4

import numpy as np
import h5py
import math

comm = None
comm_rank = None
comm_size = None


def init_mpi_comm(x):
    global comm, comm_rank, comm_size
    comm = x
    comm_rank = comm.Get_rank()
    comm_size = comm.Get_size()


def iter_dataset(func, filepath, contractname, windowsize, num_slippage, ticksize, varify_window, enter_r_threshold):
    """
    :param func: 计算哪种指标分布
    :param windowsize: 用于计算的窗口大小
    :param win_threshold: 盈利的阈值计算时,取滑点的个数
    :param ticksize: 最小的价格变动单位.
    :param enter_r_threshold: r的阈值，小于多少时产生入场信号。
    :return: 
    """
    with h5py.File(filepath, 'r', driver='mpio', comm=comm) as f:
        contractgrp = f.get(contractname, None)
        if contractgrp is None:
            return
        for grp in contractgrp.values():
            prob = grp.get('expo_dist_forecast_{}_{}'.format(windowsize, num_slippage))
            varify = grp.get('varification_{}_{}'.format(windowsize, num_slippage))
            parse_data(func, f, prob, varify, windowsize, num_slippage, ticksize, varify_window, enter_r_threshold)
            comm.bcast('for synchronization' if comm_rank == 0 else None, root=0)


def parse_data(func, f_handle, prob, varify, windowsize, num_slippage, ticksize, varify_window, enter_r_threshold):
    """
    :param func: 计算哪种指标分布
    :param spread: h5py.DataSet
    :return: 
    """

    grp = prob.parent
    length = grp.attrs.get('length')

    local_data_offset = np.linspace(0, length - windowsize, comm_size, False).astype(np.int32)
    startpoint = local_data_offset[comm_rank]
    if comm_rank + 1 == comm_size:
        endpoint = None
    else:
        endpoint = varify_window + local_data_offset[comm_rank+1]

    exp_data = prob.value[startpoint + windowsize: endpoint, [0, 2, 3, 4]]
    varify_data = varify.value[startpoint + windowsize: endpoint]
    # print 'group: {}, length: {}, rank: {}, offsets: {}--{}'.format(grp.name, length, comm_rank, startpoint, endpoint)

    res = func(exp_data, varify_data, varify_window, enter_r_threshold, ticksize)

    # 等一下，集合每一个res（字典），算总的res。
    res = comm.gather(res, root=0)
    if comm_rank == 0:
        totalres = {}
        for item in res:
            for k in item.iterkeys():
                totalres[k] = totalres.setdefault(k, 0) + item[k]

        print totalres, '...windowsize:', windowsize, '...number of slippage:', num_slippage, 'enter r thred:', enter_r_threshold


def distribution_1(expdata, varifydata, varify_window, enter_r_threshold, ticksize):

    if len(expdata) != len(varifydata):
        raise '数据长度不一致!'

    resdict = {}
    idx = 0
    while idx < len(expdata) - varify_window:
        if varifydata[idx] - 1 != 0 or expdata[idx, 2] > enter_r_threshold or expdata[idx, 2] < 0:
            idx += 1
            continue
        origin = expdata[idx:idx + varify_window + 1, 0]
        longshort = expdata[idx, 1]

        # print idx, origin[0], expdata[idx, 3]

        if math.fabs(longshort - 1) < 0.00001:
            upbound = origin[0] + expdata[idx, 3]
            for counter, item in enumerate(origin[1:]):
                if item < upbound:
                    res = int((item - origin[0]) / ticksize)
                    resdict[res] = resdict.setdefault(res, 0) + 1
                else:
                    idx += counter + 1
                    break
        else:
            downbound = origin[0] - expdata[idx, 3]
            for counter, item in enumerate(origin[1:]):
                if item > downbound:
                    res = int((origin[0] - item) / ticksize)
                    resdict[res] = resdict.setdefault(res, 0) + 1
                else:
                    idx += counter + 1
                    break

    return resdict


def distribution_2(expdata, varifydata, varify_window, enter_r_threshold, ticksize):

    if len(expdata) != len(varifydata):
        raise '数据长度不一致!'

    resdict = {}
    idx = 0
    while idx < len(expdata) - varify_window:
        if varifydata[idx] - 1 != 0 or expdata[idx, 2] > enter_r_threshold or expdata[idx, 2] < 0:
            idx += 1
            continue
        origin = expdata[idx:idx + varify_window + 1, 0]
        longshort = expdata[idx, 1]

        if math.fabs(longshort - 1) < 0.00001:
            upbound = origin[0] + expdata[idx, 3]
            min_res = 0
            for counter, item in enumerate(origin[1:]):
                if item < upbound:
                    res = int((item - origin[0]) / ticksize)
                    if res < min_res:
                        min_res = res
                else:
                    idx += counter + 1
                    break
        else:
            downbound = origin[0] - expdata[idx, 3]
            min_res = 0
            for counter, item in enumerate(origin[1:]):
                if item > downbound:
                    res = int((origin[0] - item) / ticksize)
                    if res < min_res:
                        min_res = res
                else:
                    idx += counter + 1
                    break

        resdict[min_res] = resdict.setdefault(min_res, 0) + 1

    return resdict


def distribution_3(expdata, varifydata, varify_window, enter_r_threshold, ticksize):

    if len(expdata) != len(varifydata):
        raise '数据长度不一致!'

    resdict = {}
    idx = 0
    while idx < len(expdata) - varify_window:
        if varifydata[idx] - 1 == 0 or expdata[idx, 2] > enter_r_threshold or expdata[idx, 2] < 0:
            idx += 1
            continue
        origin = expdata[idx:idx + varify_window + 1, 0]
        longshort = expdata[idx, 1]

        if math.fabs(longshort - 1) < 0.00001:
            res = int((origin[-1] - origin[0]) / ticksize)
        else:
            res = int((origin[0] - origin[-1]) / ticksize)

        resdict[res] = resdict.setdefault(res, 0) + 1

        idx += 1

    return resdict


def distribution_4(expdata, varifydata, varify_window, enter_r_threshold, ticksize):

    if len(expdata) != len(varifydata):
        raise '数据长度不一致!'

    resdict = {}
    idx = 0
    while idx < len(expdata) - varify_window:
        if varifydata[idx] - 1 == 0 or expdata[idx, 2] > enter_r_threshold or expdata[idx, 2] < 0:
            idx += 1
            continue
        origin = expdata[idx:idx + varify_window + 1, 0]
        longshort = expdata[idx, 1]

        # print idx, origin[0], expdata[idx, 3]

        if math.fabs(longshort - 1) < 0.00001:
            for counter, item in enumerate(origin[1:]):
                res = int((item - origin[0]) / ticksize)
                resdict[res] = resdict.setdefault(res, 0) + 1

        else:
            for counter, item in enumerate(origin[1:]):
                res = int((origin[0] - item) / ticksize)
                resdict[res] = resdict.setdefault(res, 0) + 1

        idx += 1

    return resdict
