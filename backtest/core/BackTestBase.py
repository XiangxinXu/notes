# coding=utf-8

from threading import Thread
from ..core.BackTestEngine import BackTestEngine
from ..core.DataRecorder import DataRecorder
from ..core.common import *
from ..utils.DataBuffer import FixedBuffer
from time import clock


class BackTestBase(Thread):
    def __init__(self,
                 start,
                 end,
                 symbols,
                 mode=BACK_TEST_MODE_ONBAR,
                 time_step=TIME_STEP_1MINUTE,
                 market_type=MARKET_TYPE_FOREX,
                 balance=10000,
                 leverage=100,
                 eventhandler_enabled=False):
        self.eventhandler_enabled = eventhandler_enabled                      # 是否使用事件句柄处理事件
        super(BackTestBase, self).__init__()
        self.symbols = symbols
        self.time_step = time_step
        self.mode = mode
        self.balance = balance
        self.leverage = leverage
        self.engine = BackTestEngine(self, start, end, self.symbols, mode, time_step, market_type, balance, leverage)
        self.allocation_succeed = False
        self.indicator_buffers = {}

        if self.eventhandler_enabled:
            self.event_handler = self.engine.get_event_handler()       # 事件处理句柄
            self.data_recorder = DataRecorder(self)                    # 用数据记录者包装onbar和ontick函数
            self.on_bar = self.data_recorder.onbar(self.on_bar)        # 包装后的onbar和ontick加入了数据记
            self.on_tick = self.data_recorder.ontick(self.on_tick)     # 录者的数据记录功能
        else:
            self.event_handler = None
            self.data_recorder = None

        self._exhibitor = None

    def register_event(self, **kwargs):
        """
        注册自定义的事件处理函数
        Parameters
        ----------
        kwargs：要注册的事件
        """
        self.event_handler.register_processor(**kwargs)

    def on_event(self, **kwargs):
        """
        在自定义事件到来时的处理函数
        自定义事件的处理函数必须在初始化时进行注册：使用register_event()
        Parameters
        ----------
        kwargs：待处理的事件
        """
        self.event_handler.on_event(**kwargs)

    def set_exhibitor(self, exhibitor):
        self._exhibitor = exhibitor
        if self.eventhandler_enabled:
            self.data_recorder.set_exhibitor(self._exhibitor)

    def exit_backtest(self):
        self.engine.stop()

    def run(self):
        start = clock()
        if self.allocation_succeed:
            if self.eventhandler_enabled:
                self.event_handler.start()
            self.engine.run()
            if self.eventhandler_enabled:
                self.data_recorder.on_finish()  # 回测结束后调用数据记录者的on_finish()函数
                self.event_handler.stop()
        else:
            raise RuntimeError(BUFFER_NOT_ALLOCATED)
        print(clock() - start)
        print('equity: ', self.get_equity())

    def on_bar(self, date_time):
        """
        date_time:当前bar的时间, datetime类型
        """
        pass

    def on_tick(self, ask, bid, symbol, date_time):
        """
        ask: 数字
        bid: 数字
        symbol: 字符串类型
        date_time: datetime类型
        """
        pass

    def send_order(self, strategy_id, symbol, price, volume, order_type, slippage):
        """
        发送订单
        Parameters
        ----------
        strategy_id: 策略名或编号，建议字符串或整型
        symbol: 品种代码，字符串常量
        price: 价格
        volume: 手数
        order_type: ORDER_BUY 或者 ORDER_SELL
        slippage: 滑点

        Returns
        -------
        订单编号
        """
        return self.engine.send_order(symbol, price, volume, order_type, slippage, strategy_id)

    def close_order(self, order, price, volume):
        """
        发送关闭订单
        Parameters
        ----------
        order: 待平仓的订单
        volume: 手数
        price: 平仓价格

        Returns
        -------
        ORDER_STATE_PENDING则挂单成功，否则不成功
        """
        return self.engine.close_order(order, price, volume)

    def cancel_order(self, order):
        """
        取消订单
        Parameters
        ----------
        order: 待取消订单

        Returns
        -------
        order的状态，正常取消则为ORDER_STATE_CANCELLED
        """
        return self.engine.cancel_order(order)

    def get_orders(self, symbol):
        """
        返回所有未平仓的订单。
        Parameters
        ----------
        symbol: 品种代码，字符串常量

        Returns
        -------
        所有的订单列表。
        """
        return self.engine.get_position_orders(symbol)

    def get_history_orders_by_symbol(self, symbol):
        """
        按订单种类返回所有的历史订单
        Parameters
        ----------
        symbol：订单符号

        Returns
        -------
        历史订单列表
        """
        return self.engine.get_history_orders_by_symbol(symbol)

    def get_history_orders_by_strategy_id(self, strategy_id):
        """
        按策略编码返回所有历史订单
        Parameters
        ----------
        strategy_id：策略编码

        Returns
        -------
        历史订单列表
        """
        return self.engine.get_history_order_by_strategyid(strategy_id)

    def get_pending_orders(self):
        """
        返回所有未成交订单
        Returns
        -------
        所有未成交订单列表
        """
        return self.engine.get_pending_orders()

    def get_closed_orders(self):
        """
        返回所有已平仓订单
        Returns
        -------
        所有已平仓订单列表
        """
        return self.engine.get_closed_orders()

    def get_cancelled_orders(self):
        """
        返回所有已取消订单
        Returns
        -------
        所有已取消订单列表
        """
        return self.engine.get_cancelled_orders()

    def get_history_orders(self):
        """返回所有的历史订单（包括取消订单和未成交订单）
        Returns
        _______
        所有历史订单列表
        """
        return self.engine.get_history_orders()

    def get_history_effective_orders(self):
        """
        返回所有的历史有效订单（即已平仓订单和在仓位中的订单）
        Returns
        -------
        所有的历史有效订单列表
        """
        return self.engine.get_history_effective_orders()

    def get_equity(self):
        """
        获取当前的账户资金净值
        Returns
        -------
        当前账户资金净值
        """
        return self.engine.get_equity()

    def get_data(self, symbol, period, data_type):
        """
        取‘开高低收时间成交量’数据
        :param symbol: 产品代码
        :param period: 周期
        :param data_type: BUFFER_OPEN...
        :return: 一个FixedBuffer。
        """
        return self.engine.get_data(symbol, period, data_type)

    def allocate_data_buffers(self, symbol, period, data_type, buffer_size):
        """
        分配数据数组。若分配失败则不能进行回测。
        :param symbol: 产品代码
        :param period: 周期
        :param data_type: 字符串，由'O','H','L','C','V','T'中任意字符组成，分别代表开，高，低，收，量，时间。
        :param buffer_size: 缓存大小
        :return: None
        """
        if period < self.time_step:
            raise ValueError(TIME_PERIOD_VALUE_ERROR)
        index_direction = REVERSED_INDEXING
        if BUFFER_OPEN in data_type:
            data_buffer = FixedBuffer(buffer_size, index_direction)
            self.engine.add_buffers(symbol, data_buffer, BUFFER_OPEN, period)
        if BUFFER_HIGH in data_type:
            data_buffer = FixedBuffer(buffer_size, index_direction)
            self.engine.add_buffers(symbol, data_buffer, BUFFER_HIGH, period)
        if BUFFER_LOW in data_type:
            data_buffer = FixedBuffer(buffer_size, index_direction)
            self.engine.add_buffers(symbol, data_buffer, BUFFER_LOW, period)
        if BUFFER_CLOSE in data_type:
            data_buffer = FixedBuffer(buffer_size, index_direction)
            self.engine.add_buffers(symbol, data_buffer, BUFFER_CLOSE, period)
        if BUFFER_VOLUME in data_type:
            data_buffer = FixedBuffer(buffer_size, index_direction)
            self.engine.add_buffers(symbol, data_buffer, BUFFER_VOLUME, period)
        if BUFFER_TIME in data_type:
            data_buffer = FixedBuffer(buffer_size, index_direction)
            self.engine.add_buffers(symbol, data_buffer, BUFFER_TIME, period)
        self.allocation_succeed = True

    def allocate_indicator_buffers(self, name, buffer_size, mode):
        """
        分配指标数组。
        :param name: 数组名称
        :param buffer_size: 数组大小
        :param mode: 逆序还是顺序
        :return: None
        """
        bf = FixedBuffer(buffer_size, mode)
        self.indicator_buffers[name] = bf
