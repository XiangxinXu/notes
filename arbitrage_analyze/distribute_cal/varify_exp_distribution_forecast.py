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


def iter_dataset(filepath, contractname, windowsize, num_slippage, ticksize, varify_window):
    """
    :param windowsize: 用于计算的窗口大小
    :param win_threshold: 盈利的阈值计算时,取滑点的个数
    :param ticksize: 最小的价格变动单位.
    :return: 
    """
    with h5py.File(filepath, 'a', driver='mpio', comm=comm) as f:
        contractgrp = f.get(contractname, None)
        if contractgrp is None:
            return
        for grp in contractgrp.values():
            prob = grp.get('expo_dist_forecast_{}_{}'.format(windowsize, num_slippage))
            parse_data(f, prob, windowsize, num_slippage, ticksize, varify_window)
            comm.bcast('for synchronization' if comm_rank == 0 else None, root=0)


def parse_data(f_handle, prob, windowsize, num_slippage, ticksize, varify_window):
    """
    :param spread: h5py.DataSet
    :return: 
    """

    grp = prob.parent
    length = grp.attrs.get('length')

    local_data_offset = np.linspace(0, length, comm_size, False).astype(np.int32)
    startpoint = local_data_offset[comm_rank]
    if comm_rank + 1 == comm_size:
        endpoint = None
    else:
        endpoint = varify_window + local_data_offset[comm_rank+1]

    local_data = prob.value[startpoint: endpoint, [0, 2, 3, 4]]
    print 'group: {}, length: {}, rank: {}, offsets: {}--{}'.format(grp.name, length, comm_rank, startpoint, endpoint)

    res = calculation(local_data, varify_window)

    if len(res) == length:
        print grp.name, 'finished. length is ', length
    else:
        raise 'xxxxxxx'

    data2h5file(f_handle, grp, res, windowsize, num_slippage, varify_window)


def calculation(local_data, varify_window):
    datas = np.asarray([0] * (len(local_data) - varify_window), dtype=np.int8)

    for idx in xrange(len(local_data) - varify_window):
        origin = local_data[idx:idx+varify_window+1, 0]
        longshort = local_data[idx, 1]
        prob = local_data[idx, 2]
        win_thrsh = local_data[idx, 3]

        haschance = 0
        if math.fabs(longshort - 1) < 0.00001:
            upbound = origin[0] + win_thrsh
            for item in origin[1:]:
                if item >= upbound:
                    haschance = 1
                    break
        else:
            downbound = origin[0] - win_thrsh
            for item in origin[1:]:
                if item <= downbound:
                    haschance = 1
                    break

        datas[idx] = haschance

        if idx % 10000 == 0:
            print idx, '...', comm_rank, '_rank.'

    res = comm.allgather(datas)

    res = np.hstack(res)
    res = np.hstack([res, np.asarray([-1] * varify_window)])
    return res


def data2h5file(f_handle, grp, data, windowsize, num_slippage, varify_window):
    name = 'varification_{}_{}'.format(windowsize, num_slippage)
    ds = grp.create_dataset(name, shape=data.shape, dtype=np.int8, data=data)
    ds.attrs.create('note', 'window size: {}, number of slippage: {}, varify window size: {}.'
                            'can win threshold be reached in a varify window.'
                    .format(windowsize, num_slippage, varify_window))
    f_handle.flush()


