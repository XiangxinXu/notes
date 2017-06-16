# coding=utf-8

import exp_distribution
import varify_exp_distribution_forecast
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

    for item in dic:

        contractname = item['name']
        fee_rate_min = item['fee_rate_min']
        fee_rate_max = item['fee_rate_max']
        ticksize = item['ticksize']
        con_multiplier = item['contract_multiplier']

        for window_size in winsize:
            for num_slippage in num_slippages:
                exp_distribution.init_mpi_comm(comm)
                exp_distribution.iter_dataset(filepath, contractname, window_size, num_slippage, ticksize, fee_rate_min, fee_rate_max, con_multiplier)
                comm.bcast('for synchronization' if comm.Get_rank() == 0 else None, root=0)

        for window_size in winsize:
            varify_window = window_size / 4
            for num_slippage in num_slippages:
                varify_exp_distribution_forecast.init_mpi_comm(comm)
                varify_exp_distribution_forecast.iter_dataset(filepath, contractname, window_size, num_slippage, ticksize, varify_window)
                comm.bcast('for synchronization' if comm.Get_rank() == 0 else None, root=0)


