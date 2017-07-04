# coding=utf-8

import numpy as np
import h5py
import matplotlib
matplotlib.use("agg")
from matplotlib import pyplot as plt
import seaborn as sns
import math

outputpath = './figures/'
f = h5py.File('./future_spread_arbitrage.h5', 'r')

for distribution in (1, 2, 3, 4):
    for contract in f.itervalues():
        contractname = contract.name[1:]
        for subgrp in contract.itervalues():
            print subgrp.name
            print distribution

            idx = -1
            fig, axes = plt.subplots(3, 6, sharey=True, sharex=True)
            for data in subgrp.itervalues():

                for i in range(axes.shape[0]):
                    for j in range(axes.shape[1]):
                        if i == 2:
                            axes[i, j].set_xlabel('tick deltas')
                        if j == 0:
                            axes[i, j].set_ylabel('percentage')

                if 'dis' + str(distribution) in data.name:
                    idx += 1

                    # 过滤掉一些异常值.
                    d = {}
                    for idxx in xrange(data.value.shape[1]):
                        d[data.value[0][idxx]] = data.value[1][idxx]

                    topopoutlist = []
                    for key in d.iterkeys():
                        if math.fabs(key) >= 20:
                            topopoutlist.append(key)
                    for item in topopoutlist:
                        d.pop(item)

                    windsize = data.name.split(':')[1].split('_')[0]
                    ns = data.name.split(':')[2].split('_')[0]
                    ert = data.name.split(':')[3]
                    l = [(k, d[k]) for k in d.iterkeys()]
                    if len(l) == 0:
                        x, y = [], []
                    else:
                        x, y = zip(*l)
                        y = y / sum(y)

                    barwidth = 0.8
                    axes[idx/6][idx%6].bar(np.asarray(x) - barwidth / 2., y, barwidth)
                    axes[idx/6][idx%6].tick_params(labelsize=4)

                    axes[idx/6][idx%6].text(-18, 0.18, 'window size:{}\nnumber of slippage:{}\nr threshold:{}'.format(windsize, ns, ert),
                                            fontsize=6, alpha=0.6)
            axes[0][2].set_title(contractname + '----' + subgrp.name.split('/')[-1] + ' ' + 'distribution {}.'.format(distribution))
            plt.xlim(-20, 10)
            plt.subplots_adjust(wspace=0.02, hspace=0.02)
            plt.savefig(outputpath+(subgrp.name.split('/')[2]) + 'distribution' + str(distribution) +'.pdf')
            plt.close()
