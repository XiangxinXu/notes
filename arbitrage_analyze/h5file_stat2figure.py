import h5py
import matplotlib as mpl
mpl.use('agg')
from matplotlib import pyplot as plt
import seaborn as sns
import numpy as np
import re

dt1 = ['1501-1505', '1505-1509', '1509-1601', '1601-1605', '1605-1609', '1609-1701', '1701-1705', '1705-1709']
dt2 = ['1501-1505', '1505-1510', '1510-1601', '1601-1605', '1605-1610', '1610-1701', '1701-1705', '1705-1710']
dt3 = ['1509-1512', '1512-1603', '1603-1606', '1606-1609', '1609-1612', '1612-1703', '1703-1706', '1706-1709']
dt4 = ['1312-1403', '1403-1406', '1406-1409', '1409-1412', '1412-1503', '1503-1506', '1506-1509',
       '1509-1512', '1512-1603', '1603-1606', '1606-1609', '1609-1612', '1612-1703', '1703-1706', '1706-1709']
parentpath = 'C:/users/xxx/desktop/result/'
f = h5py.File(parentpath+'future_spread_arbitrage.h5', 'r')

ratio_threshold = [0.1, 0.3, 0.5]


def get_result_dict_from_h5file(f):
    allresult = {}

    for contract in f.itervalues():
        contractname = contract.name[1:]
        winsizeset = set()
        winthrhset = set()

        for subgrp in contract.itervalues():
            for data in subgrp.iterkeys():
                if 'expo' in data:
                    windowsize = data.split('_')[-2]
                    win_thrsh = data.split('_')[-1]
                    winsizeset.add(windowsize)
                    winthrhset.add(win_thrsh)
            break
        res = {}
        for i in winsizeset:
            for j in winthrhset:
                listname = 'ws' + str(i) + 'wth' + str(j)
                res[listname] = {}
                for r in ratio_threshold:
                    res[listname]['r=' + str(r)] = {'orr': [], 'ocr': [], 'oof': []}

        for subgrp in contract.itervalues():
            for data in subgrp.itervalues():
                if 'expo' in data.name:
                    winsize = data.name.split('_')[-2]
                    winthrsh = data.name.split('_')[-1]
                    for r in ratio_threshold:
                        orr = data.attrs.get('open right ratio(r={})'.format(r))
                        ocr = data.attrs.get('opportunity catch ratio(r={})'.format(r))
                        oof = data.attrs.get('open opportunity frequency(r={})'.format(r))
                        res['ws' + str(winsize) + 'wth' + str(winthrsh)]['r=' + str(r)]['orr'].append(orr)
                        res['ws' + str(winsize) + 'wth' + str(winthrsh)]['r=' + str(r)]['ocr'].append(ocr)
                        res['ws' + str(winsize) + 'wth' + str(winthrsh)]['r=' + str(r)]['oof'].append(oof)

        allresult[contractname] = res

    f.close()
    return allresult


def draw_result_dict(dct):
    fig = plt.figure()
    xtickitem = dt2
    xtickitemnum = len(xtickitem)

    for contr in ['rb', 'hc']:
        contract = dct[contr]
        for itemname, item in contract.iteritems():

            windowsize = re.findall('(\d+)', itemname)[0]
            num_slippage = re.findall('(\d+)', itemname)[1]
            title = 'window size:{}, number of slippage:{}, lasting time(s):{}'.format(windowsize, num_slippage,
                                                                                  int(windowsize) / 4)
            orr = []
            ocr = []
            oof = []
            for r in [0.1, 0.3, 0.5]:
                orr.append(item['r=' + str(r)]['orr'])
                ocr.append(item['r=' + str(r)]['ocr'])
                oof.append(item['r=' + str(r)]['oof'])
            fig = plt.figure()
            ax1 = fig.add_subplot(3, 1, 1)
            ax2 = fig.add_subplot(3, 1, 2)
            ax3 = fig.add_subplot(3, 1, 3)
            width = 0.25
            cls = ['#e8ffc4', '#ffeedd', '#a3d1d1']
            for i, r in enumerate(ratio_threshold):
                ax1.bar(np.arange(xtickitemnum) + i * width, orr[i], width, color=cls[i], alpha=0.8, label='r=' + str(r))
                ax2.bar(np.arange(xtickitemnum) + i * width, ocr[i], width, color=cls[i], alpha=0.8, label='r=' + str(r))
                ax3.bar(np.arange(xtickitemnum) + i * width, oof[i], width, color=cls[i], alpha=0.8, label='r=' + str(r))
            ax1.legend(fontsize='x-small')
            ax2.legend(fontsize='x-small')
            ax3.legend(fontsize='x-small')
            ax1.set_title('contract:' + contr + '\n' + title)
            ax1.set_xticks(np.arange(xtickitemnum) + 2 * width)
            ax2.set_xticks(np.arange(xtickitemnum) + 2 * width)
            ax3.set_xticks(np.arange(xtickitemnum) + 2 * width)
            ax1.set_xticklabels(xtickitem, rotation=15, fontsize='small')
            ax2.set_xticklabels(xtickitem, rotation=15, fontsize='small')
            ax3.set_xticklabels(xtickitem, rotation=15, fontsize='small')
            ax1.set_ylim([0, 1])
            ax2.set_ylim([0, 1])
            ax3.set_ylim([0, 1])
            ax1.set_ylabel('orr')
            ax2.set_ylabel('ocr')
            ax3.set_ylabel('oof')
            plt.subplots_adjust(hspace=0.43)
            plt.savefig(parentpath + contr + '_' + str(int(windowsize) / 4) + '_' + num_slippage + '.pdf')


draw_result_dict(get_result_dict_from_h5file(f))
