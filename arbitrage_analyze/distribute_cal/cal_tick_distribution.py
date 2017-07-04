# coding=utf-8

import tick_distribution
from tick_distribution import distribution_1, distribution_2, distribution_3, distribution_4
import mpi4py.MPI as MPI
import json

#
#  Global variables for MPI
#

# instance for invoking MPI related functions
comm = MPI.COMM_WORLD


if __name__ == '__main__':

    filepath = '../future_spread_arbitrage.h5'
    configfile = 'contract_info'

    with open(configfile) as f:
        dic = json.load(f)

    winsize = [600, 1200, 1800]
    num_slippages = [3, 4]

    print 'distribution 1'
    for item in dic:

        contractname = item['name']
        fee_rate_min = item['fee_rate_min']
        fee_rate_max = item['fee_rate_max']
        ticksize = item['ticksize']
        con_multiplier = item['contract_multiplier']
        for window_size in winsize:
            for num_slippage in num_slippages:
                for r in [0.1, 0.3, 0.5]:
                    tick_distribution.init_mpi_comm(comm)
                    tick_distribution.iter_dataset(distribution_1, filepath, contractname, window_size, num_slippage, ticksize, window_size/4, r, "dis1")
                    comm.bcast('for synchronization' if comm.Get_rank() == 0 else None, root=0)

    print 'distribution 2:'
    for item in dic:

        contractname = item['name']
        fee_rate_min = item['fee_rate_min']
        fee_rate_max = item['fee_rate_max']
        ticksize = item['ticksize']
        con_multiplier = item['contract_multiplier']

        for window_size in winsize:
            for num_slippage in num_slippages:
                for r in [0.1, 0.3, 0.5]:
                    tick_distribution.init_mpi_comm(comm)
                    tick_distribution.iter_dataset(distribution_2, filepath, contractname, window_size, num_slippage, ticksize, window_size/4, r, 'dis2')
                    comm.bcast('for synchronization' if comm.Get_rank() == 0 else None, root=0)

    print 'distribution 3:'
    for item in dic:

        contractname = item['name']
        fee_rate_min = item['fee_rate_min']
        fee_rate_max = item['fee_rate_max']
        ticksize = item['ticksize']
        con_multiplier = item['contract_multiplier']

        for window_size in winsize:
            for num_slippage in num_slippages:
                for r in [0.1, 0.3, 0.5]:
                    tick_distribution.init_mpi_comm(comm)
                    tick_distribution.iter_dataset(distribution_3, filepath, contractname, window_size, num_slippage, ticksize, window_size/4, r, 'dis3')
                    comm.bcast('for synchronization' if comm.Get_rank() == 0 else None, root=0)

    print 'distribution 4:'
    for item in dic:

        contractname = item['name']
        fee_rate_min = item['fee_rate_min']
        fee_rate_max = item['fee_rate_max']
        ticksize = item['ticksize']
        con_multiplier = item['contract_multiplier']

        for window_size in winsize:
            for num_slippage in num_slippages:
                for r in [0.1, 0.3, 0.5]:
                    tick_distribution.init_mpi_comm(comm)
                    tick_distribution.iter_dataset(distribution_4, filepath, contractname, window_size, num_slippage, ticksize, window_size/4, r, 'dis4')
                    comm.bcast('for synchronization' if comm.Get_rank() == 0 else None, root=0)