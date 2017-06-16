# coding=utf-8

import h5py


def f(a, b, r=0.5):
    pc = 0
    tc = 0
    for i in xrange(len(a)):
        if 0 < a[i] < r:
            pc += 1
            if b[i] == 1:
                tc += 1
    if pc == 0:
        return -1
    return float(tc)/pc


def g(a, b, r=0.5):
    tc = 0
    pc = 0
    for i in xrange(len(a)):
        if b[i] == 1:
            tc += 1
            if 0 < a[i] < r:
                pc += 1
    if tc == 0:
        return -1
    return float(pc) / tc


def freq1(a, r=0.5):
    c = 0
    for i in a:
        if 0 < i < r:
            c += 1
    return float(c)/len(a)

if __name__ == '__main__':

    f5 = h5py.File('./future_spread_arbitrage.h5', 'a')
    for r in (0.5, 0.3, 0.1):
        for contr in f5.itervalues():
            for x in contr.itervalues():
                for y in x.itervalues():
                    if 'expo' in y.name:
                        windowsize, win_thrsh = y.name.split('_')[-2], y.name.split('_')[-1]
                        prob = y[:, 3]
                        tv = x.get('varification_{}_{}'.format(windowsize, win_thrsh))[:]
                        print y.name, 'r', r
                        y.attrs.create('open right ratio(r={})'.format(r), data=f(prob, tv, r))
                        y.attrs.create('opportunity catch ratio(r={})'.format(r), data=g(prob, tv, r))
                        y.attrs.create('open opportunity frequency(r={})'.format(r), data=freq1(prob, r))
    f5.close()
