# coding=utf-8

from datetime import datetime, timedelta

from PyQt4.QtCore import pyqtSignal, QObject, pyqtSlot
from matplotlib import ticker
from ..core.common import *


is_ui_enabled = UI_DISABLED


def ui_bonded_func(func):
    def wrapper(*args, **kwargs):
        if is_ui_enabled:  # 若开启了UI，才执行相关的UI更新操作
            ret = func(*args, **kwargs)
            return ret
        else:
            return None
    return wrapper


class SignalWrapper(QObject):
    equity_plot_refresh = pyqtSignal()
    equity_label_refresh = pyqtSignal(float, datetime)
    max_draw_back_label_refresh = pyqtSignal(float, datetime)
    order_number_refresh = pyqtSignal(int)
    set_show_time = pyqtSignal(datetime)
    total_order_number = pyqtSignal(int)
    profit_order_number = pyqtSignal(int)
    loss_order_number = pyqtSignal(int)
    gross_profit = pyqtSignal(float)
    gross_loss = pyqtSignal(float)
    total_profit = pyqtSignal(float)
    order_info = pyqtSignal(list)


class DataRecorder(object):
    """
    用来记录历史数据。
    在回测中用来包装onbar或ontick方法。
    加入记录数据的功能。
    """

    # is_ui_enabled = UI_DISABLED

    def __init__(self, backtestbase):
        self._backtest_base = backtestbase
        self._mode = self._backtest_base.mode
        if self._mode == BACK_TEST_MODE_ONBAR:
            self._func = self._backtest_base.on_bar
        elif self._mode == BACK_TEST_MODE_ONTICK:
            self._func = self._backtest_base.on_tick
        else:
            raise TypeError(MODE_TYPE_ERROR)
        self.register_event()
        self.date_time = datetime(1900, 1, 1)
        self.last_datetime = datetime(1900, 1, 1)
        self._ui_refresh_rate = timedelta(hours=8)

        self._exhibitor = None

        self._max_equity = 0
        self._max_equity_time = None

        self._drawdown = 0
        self._max_drawdown = 0
        self._drawdown_rate = 0
        self._max_drawdown_rate = 0
        self._max_drawdown_time = None

        self._gross_profit = 0
        self._gross_loss = 0
        self._profit_order_numbers = 0
        self._loss_order_numbers = 0
        self._profit = 0
        self._profit_rate = 0

        self._equity_buffer = []
        self._equity_time_buffer = []

        self._signals = SignalWrapper()
        self._connect_signals()

    def _connect_signals(self):
        self._signals.equity_plot_refresh.connect(self.refresh_equity_axis)
        self._signals.equity_label_refresh.connect(self.refresh_equity_labels)
        self._signals.max_draw_back_label_refresh.connect(self.refresh_drawback_labels)
        self._signals.order_number_refresh.connect(self.refresh_order_number_label)
        self._signals.set_show_time.connect(self.refresh_show_time_label)
        self._signals.total_order_number.connect(self.set_total_order_number)
        self._signals.gross_loss.connect(self.set_gross_loss)
        self._signals.gross_profit.connect(self.set_gross_profit)
        self._signals.profit_order_number.connect(self.set_profit_order_number)
        self._signals.loss_order_number.connect(self.set_loss_order_number)
        self._signals.total_profit.connect(self.set_profit)
        self._signals.order_info.connect(self.set_order_infos)

    def register_event(self):
        """
        在这里添加要注册的事件
        Returns
        -------
        None
        """
        self._register_event(DATARECORD_EQUITY=self.on_equity_refresh)
        self._register_event(DATARECORD_ORDERNUM=self.on_order_num_refresh)
        self._register_event(DATARECORD_TIME=self.on_time_refresh)

    def record_data(self):
        """
        在这里添加要处理的事件
        Returns
        -------
        None
        """
        self._on_event(DATARECORD_EQUITY=self._backtest_base.get_equity())
        if self.date_time - self.last_datetime > self._ui_refresh_rate:
            self._on_event(DATARECORD_ORDERNUM=len(self._backtest_base.get_history_effective_orders()))
            self._on_event(DATARECORD_TIME=self.date_time)

    def _register_event(self, **kwargs):
        """
        调用BT中的事件注册函数
        Parameters
        ----------
        kwargs：待注册的事件
        """
        self._backtest_base.register_event(**kwargs)

    def _on_event(self, **kwargs):
        """
        调用BT中的事件处理函数
        Parameters
        ----------
        kwargs：待处理的事件
        """
        self._backtest_base.on_event(**kwargs)

    def set_exhibitor(self, exhibitor):
        self._exhibitor = exhibitor
        global is_ui_enabled
        if self._exhibitor is None:    # 该函数被调用无误时，类变量is_ui_enabled被更新为UI_ENABLED
            is_ui_enabled = UI_DISABLED
        else:
            is_ui_enabled = UI_ENABLED

    def onbar(self, func):
        return self._on_new_data(func)

    def ontick(self, func):
        return self._on_new_data(func)

    def _on_new_data(self, func):
        """
        包装了BT中的ontick和onbar，在其中插入了record_data功能。
        """
        def wrapper(*args, **kwargs):
            if not kwargs['date_time'] == self.date_time:
                self.date_time = kwargs['date_time']
                self.record_data()
                if self.date_time - self.last_datetime > self._ui_refresh_rate:
                    self.last_datetime = self.date_time
            return func(*args, **kwargs)
        return wrapper

    def on_equity_refresh(self, equity):
        """
        传入更新的账户资金净值的处理程序
        Parameters
        ----------
        equity：账户资金净值
        """
        if equity > self._max_equity:        # 刷新最大净值
            self._max_equity = equity
            self._max_equity_time = self.date_time
            self._signals.equity_label_refresh.emit(self._max_equity, self._max_equity_time)

        self._drawdown = equity - self._max_equity      # 当前回撤
        self._drawdown_rate = self._drawdown / self._max_equity

        if self._drawdown < self._max_drawdown:         # 刷新最大回撤
            self._max_drawdown = self._drawdown
            self._max_drawdown_rate = self._max_drawdown / self._max_equity
            self._max_drawdown_time = self.date_time
            self._signals.max_draw_back_label_refresh.emit(self._max_drawdown_rate, self._max_drawdown_time)

        if self.date_time - self.last_datetime > self._ui_refresh_rate:
            self._equity_buffer.extend([equity])
            self._equity_time_buffer.extend([self.date_time])

            self._signals.equity_plot_refresh.emit()

    def on_order_num_refresh(self, order_number):
        """
        传入当前已下的有效单数
        Parameters
        ----------
        order_number：有效的订单数
        """
        self._signals.order_number_refresh.emit(order_number)

    def on_time_refresh(self, dt):
        """
        用于刷新界面的时间
        """
        self._signals.set_show_time.emit(dt)

    def on_finish(self):
        """
        在回测结束时的处理程序
        """
        orders = self._backtest_base.get_closed_orders()
        for od in orders:
            if od.profit > 0.0:
                self._gross_profit += od.profit
                self._profit_order_numbers += 1
            else:
                self._gross_loss += od.profit
                self._loss_order_numbers += 1

        self._profit = self._gross_profit + self._gross_loss
        self._profit_rate = (self._profit - self._backtest_base.balance) / self._backtest_base.balance

        self._signals.total_profit.emit(self._profit)
        self._signals.gross_loss.emit(self._gross_loss)
        self._signals.gross_profit.emit(self._gross_profit)
        self._signals.profit_order_number.emit(self._profit_order_numbers)
        self._signals.loss_order_number.emit(self._loss_order_numbers)
        self._signals.total_order_number.emit(len(orders))

        self._signals.order_info.emit(orders)

    @pyqtSlot()
    @ui_bonded_func
    def refresh_equity_axis(self):
        equity_axis = self._exhibitor.get_equity_axis()
        equity_axis.hold(False)
        equity_axis.plot(self._equity_time_buffer, self._equity_buffer)
        equity_axis.set_xlabel(u'时间')
        equity_axis.set_ylabel(u'资金净值')
        equity_axis.set_title(u'资金净值变化图')
        fmt = ticker.ScalarFormatter(useMathText=True)
        equity_axis.yaxis.set_major_formatter(fmt)
        self._exhibitor.get_canvas().draw()

    @pyqtSlot()
    @ui_bonded_func
    def refresh_equity_labels(self, equity, dt):
        self._exhibitor.set_equity_labels(equity, dt)

    @pyqtSlot()
    @ui_bonded_func
    def refresh_drawback_labels(self, db, dt):
        self._exhibitor.set_drawback_labels(db, dt)

    @pyqtSlot()
    @ui_bonded_func
    def refresh_order_number_label(self, odn):
        self._exhibitor.set_order_number_label(odn)

    @pyqtSlot()
    @ui_bonded_func
    def refresh_show_time_label(self, t):
        self._exhibitor.set_current_time_label(t)

    @pyqtSlot()
    @ui_bonded_func
    def set_total_order_number(self, n):
        self._exhibitor.set_total_order_number(n)

    @pyqtSlot()
    @ui_bonded_func
    def set_gross_profit(self, pf):
        self._exhibitor.set_gross_profit(pf)

    @pyqtSlot()
    @ui_bonded_func
    def set_gross_loss(self, ls):
        self._exhibitor.set_gross_loss(ls)

    @pyqtSlot()
    @ui_bonded_func
    def set_profit_order_number(self, n):
        self._exhibitor.set_profit_order_number(n)

    @pyqtSlot()
    @ui_bonded_func
    def set_loss_order_number(self, n):
        self._exhibitor.set_loss_order_number(n)

    @pyqtSlot()
    @ui_bonded_func
    def set_profit(self, n):
        self._exhibitor.set_profit(n)

    @pyqtSlot()
    @ui_bonded_func
    def set_order_infos(self, od):
        self._exhibitor.set_order_infos(od)

