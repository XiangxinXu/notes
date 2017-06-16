# coding=utf-8

import sys
from PyQt4 import QtGui
from Backtest.backtest.core.BackTestExhibitor import ExhibitionSubWindow
from Backtest.backtest.core.BackTestBase import BackTestBase
from Backtest.backtest.core.common import *


class MyBackTest(BackTestBase):
    def __init__(self,
                 start,
                 end,
                 symbols,
                 mode=BACK_TEST_MODE_ONBAR,
                 time_step=TIME_STEP_1MINUTE,
                 market_type=MARKET_TYPE_FOREX,
                 balance=10000):
        super(MyBackTest, self).__init__(start, end, symbols, mode, time_step, market_type, balance)

        for symb in self.symbols:
            self.allocate_data_buffers(symb, TIME_STEP_1MINUTE, 'OTCHLV', 100)

        self.allocate_indicator_buffers('ma5', 10, REVERSED_INDEXING)

    def on_bar(self, date_time):
        print 'onbar'

    def on_tick(self, ask, bid, symbol, date_time):
        print 'ontick'


def test():
    from time import clock

    start = clock()
    app = QtGui.QApplication(sys.argv)
    sym = {FOREX_XAUUSD, FOREX_XAGUSD}
    # mybt = MyBackTest('20160920', '20160930', sym, mode=BACK_TEST_MODE_ONTICK, chunk_size=TIME_STEP_1DAY)
    mybt = MyBackTest('20150820', '20150920', sym, mode=BACK_TEST_MODE_ONBAR, time_step=TIME_STEP_1MINUTE)
    a = ExhibitionSubWindow(mybt)
    mybt.start()
    a.show()
    ret = app.exec_()
    finish = clock()
    t = finish - start
    print t
    sys.exit(ret)

if __name__ == "__main__":
    import cProfile

    # 把分析结果保存到文件中,不过内容可读性差...需要调用pstats模块分析结果
    cProfile.run("test()", "result")
    import pstats

    # 创建Stats对象
    p = pstats.Stats("result")

    # 按照在一个函数中累积的运行时间进行排序
    # print_stats(3):只打印前3行函数的信息,参数还可为小数,表示前百分之几的函数信息
    p.strip_dirs().sort_stats("cumulative").print_stats()
