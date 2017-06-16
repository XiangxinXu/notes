# coding=utf-8

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


def iter_dataset(filepath, contractname, windowsize, num_slippage, ticksize, fee_rate_min, fee_rate_max, contract_multiplier):
    """
    :param windowsize: 用于计算的窗口大小
    :param num_slippage: 盈利的阈值计算时,取滑点的个数
    :param ticksize: 最小的价格变动单位.
    :param fee_rate_max: 最大的手续费率
    :param fee_rate_min: 最小的手续费率
    :param contract_multiplier: 合约乘数
    :return: 
    """
    with h5py.File(filepath, 'a', driver='mpio', comm=comm) as f:
        contractgrp = f.get(contractname, None)
        if contractgrp is None:
            return
        for grp in contractgrp.values():
            spread = grp.get('spread')
            parse_data(f, spread, windowsize, ticksize, num_slippage, fee_rate_min, fee_rate_max, contract_multiplier)
            comm.bcast('for synchronization' if comm_rank == 0 else None, root=0)


def parse_data(f_handle, spread, windowsize, ticksize, num_slippage, fee_rate_min, fee_rate_max, contract_multiplier):
    """
    :param spread: h5py.DataSet
    :return: 
    """

    grp = spread.parent
    length = grp.attrs.get('length')

    local_data_offset = np.linspace(0, length, comm_size, False).astype(np.int32)
    startpoint = local_data_offset[comm_rank]
    if comm_rank + 1 == comm_size:
        endpoint = None
    else:
        endpoint = local_data_offset[comm_rank+1]

    if comm_rank != 0:
        startpoint -= windowsize
    local_data = spread.value[startpoint: endpoint]
    print 'group: {}, length: {}, rank: {}, offsets: {}--{}'.format(grp.name, length, comm_rank, startpoint, endpoint)

    res = calculation(local_data, windowsize, windowsize/4, ticksize, num_slippage, fee_rate_min, fee_rate_max, contract_multiplier)

    if len(res) == length:
        print grp.name, 'finished. length is ', length
    else:
        raise 'xxxxxxx'

    data2h5file(f_handle, grp, res, windowsize, windowsize/4, num_slippage)


def cal_meantime(a, b, s, n=5):
    """
    计算序列s中,a出现后到b出现的平均时间间隔,单位为个数.
    若a出现次数小于n次,或a出现后b出现次数小于n次,返回-1.
    :param a: 
    :param b: 
    :param s: 
    :param n: 样本出现的最小次数限制.
    :return: 
    """
    # todo 对a的统计只看前3/4的s.

    alist = []
    res = []
    for idx, x in enumerate(s):
        if math.fabs(x - a) <= 0.0001:
            alist.append(idx)
        if math.fabs(x - b) <= 0.0001:
            while alist:
                res.append(idx - alist.pop())
    if len(res) > n:
        return sum(res) / float(len(res))
    else:
        return -1


def calculation(local_data, windowsize, backtime, ticksize, num_slippage, fee_rate_min, fee_rate_max, contract_multiplier):
    datas = np.asarray([[0]*5] * (len(local_data) - windowsize), dtype=np.float32)
    win_thrsh = math.ceil(local_data.mean() * contract_multiplier * 2 * (fee_rate_max + fee_rate_min) / (ticksize * contract_multiplier)) + num_slippage
    win_thrsh = win_thrsh * ticksize

    true_win_thresh = ticksize * (int(win_thrsh/ticksize) + 1)

    for idx in xrange(len(local_data) - windowsize):
        origin = local_data[idx+windowsize]
        _min = local_data[idx:idx+windowsize].min()
        _max = local_data[idx:idx+windowsize].max()
        _mean = local_data[idx:idx+windowsize].mean()
        if origin >= _mean:
            longshort = -1
            if origin - _min >= win_thrsh:
                win_space_exist = 1
            else:
                win_space_exist = 0
        else:
            longshort = 1
            if _max - origin >= win_thrsh:
                win_space_exist = 1
            else:
                win_space_exist = 0

        if win_space_exist == 0:
            meantime = -1
            exp_prob = -1
        else:
            if longshort == -1:
                threshold = origin - true_win_thresh
            else:
                threshold = origin + true_win_thresh
            meantime = cal_meantime(origin, threshold, local_data[idx:idx+windowsize])
            exp_prob = math.exp(-1/meantime*backtime)

        datas[idx] = [origin, win_space_exist, longshort, exp_prob, win_thrsh]

        if idx % 10000 == 0:
            print idx, '...', comm_rank, '_rank.'

    res = comm.allgather(datas)

    res = np.vstack(res)
    res = np.vstack([np.asarray([[-1]*5] * windowsize), res])
    return res


def data2h5file(f_handle, grp, data, windowsize, backtime, num_slippage):
    name = 'expo_dist_forecast_{}_{}'.format(windowsize, num_slippage)
    ds = grp.create_dataset(name, shape=data.shape, dtype=np.float32, data=data)
    ds.attrs.create('note', 'window size: {}, number of slippage: {}, 5 dims are:'
                            ' spread, '
                            ' is win space exist(0, 1), long(1)/short(-1),'
                            ' exponential probability to win in {} second,'
                            ' win threshold.'
                    .format(windowsize, num_slippage, backtime))
    f_handle.flush()
