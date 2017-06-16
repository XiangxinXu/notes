# coding=utf-8

from Backtest.backtest.core.common import *
from PyQt4 import QtGui
import sys
from Backtest.backtest.core.BackTestExhibitor import ExhibitionSubWindow
from MutiBias import MutiBias

sym = {FOREX_XAUUSD}
user_strategy = MutiBias('20150720', '20160720', sym, mode=BACK_TEST_MODE_ONBAR, time_step=TIME_STEP_1MINUTE, eventhandler_enabled=True)


def entry(ui_enabled):
    if ui_enabled:
        app = QtGui.QApplication(sys.argv)
        window = ExhibitionSubWindow(user_strategy)
        user_strategy.start()
        window.show()
        ret = app.exec_()
        sys.exit(ret)
    else:
        user_strategy.run()

entry(UI_ENABLED)
# entry(UI_DISABLED)
