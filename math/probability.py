# coding=utf-8

import numpy as np
import scipy as sp
import matplotlib
matplotlib.use('qt4agg')
import matplotlib.pyplot as plt

NUMBEROFPOINTS = 10000


def sumNsquare(n):
    count = 0
    sumsquare = [0] * NUMBEROFPOINTS
    while count < n:
        v = np.random.normal(0, 1, NUMBEROFPOINTS)
        vsquare = map(lambda x: x * x, v)
        sumsquare = map(lambda x, y: x + y, vsquare, sumsquare)
        count += 1
    return sumsquare


class Bins(object):
    def __init__(self, start, end, number):
        self.__bins = [0] * number
        for ind in xrange(len(self.__bins)):
            self.__bins[ind] = []
        self.__step = (end - start) / float(number)
        self.__start = start
        self.__end = end
        self.__number = number
        self.__result = np.zeros(number)
        self.__pdlist = np.zeros(number)
        self.__inputlist = np.zeros(number)
        self.__sum = 0

    def add(self, value):
        self.__sum += 1
        n = (value - self.__start) / self.__step
        n = int(n)
        try:
            self.__bins[n].extend([value])
        except:
            print n, value, ",,,"

    def count(self):
        for ind, item in enumerate(self.__result):
            self.__result[ind] = len(self.__bins[ind])
        xcounter = self.__start + self.__step / 2.0
        for ind, itme in enumerate(self.__pdlist):
            self.__pdlist[ind] = self.__result[ind] / self.__sum
            self.__inputlist[ind] = xcounter
            xcounter += self.__step
        return self.__inputlist, self.__pdlist


v1 = np.random.normal(0, 1, NUMBEROFPOINTS)
v1square = sumNsquare(1)
vsum2square = sumNsquare(2)
vsum5square = sumNsquare(5)
vsum10square = sumNsquare(10)
vsum20square = sumNsquare(20)
vsum50square = sumNsquare(50)
chisquare1 = np.random.chisquare(1, NUMBEROFPOINTS)
chisquare2 = np.random.chisquare(2, NUMBEROFPOINTS)
chisquare5 = np.random.chisquare(5, NUMBEROFPOINTS)
chisquare10 = np.random.chisquare(10, NUMBEROFPOINTS)


bin = Bins(-4, 4, 100)
[bin.add(x) for x in v1]
x1, y1 = bin.count()

bin = Bins(0, 16, 100)
[bin.add(x) for x in v1square]
x2, y2 = bin.count()
bin = Bins(0, 16, 100)
[bin.add(x) for x in chisquare1]
x22, y22 = bin.count()

bin = Bins(0, 32, 100)
[bin.add(x) for x in vsum2square]
x3, y3 = bin.count()
bin = Bins(0, 32, 100)
[bin.add(x) for x in chisquare2]
x33, y33 = bin.count()

bin = Bins(0, 100, 100)
[bin.add(x) for x in vsum5square]
x5, y5 = bin.count()
bin = Bins(0, 100, 100)
[bin.add(x) for x in chisquare5]
x55, y55 = bin.count()

bin = Bins(0, 100, 100)
[bin.add(x) for x in vsum10square]
x10, y10 = bin.count()
bin = Bins(0, 100, 100)
[bin.add(x) for x in chisquare10]
x1010, y1010 = bin.count()

bin = Bins(0, 100, 100)
[bin.add(x) for x in vsum20square]
x20, y20 = bin.count()

bin = Bins(0, 100, 100)
[bin.add(x) for x in vsum50square]
x50, y50 = bin.count()

plt.figure()
ax1 = plt.subplot(711)
ax2 = plt.subplot(712)
ax3 = plt.subplot(713)
ax4 = plt.subplot(714)
ax5 = plt.subplot(715)
ax6 = plt.subplot(716)
ax7 = plt.subplot(717)
ax1.plot(x1, y1)
ax2.plot(x2, y2)
ax2.plot(x22, y22, color='red')
ax3.plot(x3, y3)
ax3.plot(x33, y33, color='red')
ax4.plot(x5, y5)
ax4.plot(x55, y55, color='red')
ax5.plot(x10, y10)
ax5.plot(x1010, y1010, color='red')
ax6.plot(x20, y20)
ax7.plot(x50, y50)
plt.show()
