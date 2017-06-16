# coding=utf-8

import sys
from collections import OrderedDict
from datetime import datetime, timedelta

from ..core.DataGenerator import DataGenerator
from ..core.common import *
from ..utils.EventProcessor import EventProcessor


class OrderBase(object):
    """
    订单基类，包装了volume--〉lots和slippage。
    对内应用对应品种的volume和slippage。
    Order外部提供统一的lots和slippage操作，volume和应用在价格上的slippage对外不可见。
    """
    # 手数的倍数
    volume_mapper = {FOREX_XAUUSD: 100., FOREX_XAGUSD: 1000.}

    # 滑点的倍数
    slippage_mapper = {FOREX_XAUUSD: 0.01, FOREX_XAGUSD: 0.001}


class Order(OrderBase):
    """
    开仓订单
    """

    ORDERCOUNT = 0                          # 订单数统计

    def __init__(self, symbol, order_type, price, lots, slippage, dt, strategy_id):
        self._order_id = 'order' + str(Order.ORDERCOUNT)  # 订单编号
        Order.ORDERCOUNT += 1
        self._symbol = symbol            # 合约代码
        self._type = order_type          # 报单方向
        self._price = float(price)       # 报单价格
        self._lots = lots                # 下单手数
        self._volume = round(lots, 0.01) * Order.volume_mapper[symbol]   # 报单总数量
        self._slippage = slippage * Order.slippage_mapper[symbol]          # 滑点
        if self._type == ORDER_BUY:
            self._price_with_slippage = self._price + self._slippage
        else:
            self._price_with_slippage = self._price - self.slippage
        self._cost = self._price_with_slippage * self._volume  # 成本
        self._profit = 0                   # 平仓部分所得收益
        self._remained_value = 0           # 未平仓部分的当前价值，多单为正，空单为负
        self._order_time = dt              # 发单时间
        self._traded_volume = 0.0          # 报单成交数量
        self._remained_volume = self._volume  # 未成交数量
        self._state = ORDER_STATE_PENDING  # 订单状态
        self.__close_time_list = []         # 订单平仓时间列表，因为一个仓位可能分多次平仓，故用列表记录每次平仓时间。
        self.__close_profit_list = []       # 订单平仓收益列表，因为一个仓位可能分多次平仓，故用列表记录每次平仓收益。
        self._strategy_id = strategy_id    # 下单的策略编号

    def __str__(self):
        res = []
        if self._type == ORDER_BUY:
            tp = 'type buy,'
        else:
            tp = 'type sell,'
        res.append(tp)
        if self._state == ORDER_STATE_PENDING:
            st = 'state pending,'
        elif self._state == ORDER_STATE_IN_POSITION:
            st = 'state in_position,'
        elif self._state == ORDER_STATE_CANCELLED:
            st = 'state cancel,'
        else:
            st = 'state closed,'
        res.append(st)
        side = 'close_order,' if isinstance(self, CloseOrder) else 'normal_order,'
        vo = 'lots: {0},'.format(self.lots)
        tvo = 'traded lots: {0},'.format(self.lots_remaining)
        pf = 'profit: {0},'.format(self.profit)
        sb = 'symbol: {0},'.format(self.symbol)
        strid = 'strategy id: {0},'.format(self.strategy_id)
        oid = 'id: {0},'.format(self.order_id)
        prc = 'price: {0},'.format(self.price)
        tm = 'time: {0},'.format(self._order_time)
        res.extend([side, vo, tvo, pf, sb, strid, oid, prc, tm])
        return '  '.join(res)

    @property
    def order_id(self):
        return self._order_id

    @property
    def state(self):
        return self._state

    # 对外暴露的是加上滑点后的真实价格
    @property
    def price(self):
        return self._price_with_slippage

    # 下单成本
    @property
    def cost(self):
        return self._cost

    # 下单手数
    @property
    def lots(self):
        return self._lots

    # 未平仓剩余的手数
    @property
    def lots_remaining(self):
        return self._remained_volume / Order.volume_mapper[self._symbol]
    
    @property
    def symbol(self):
        return self._symbol

    # 买还是卖
    @property
    def type(self):
        return self._type

    @property
    def order_time(self):
        return self._order_time

    @property
    def close_time(self):
        return self.__close_time_list

    # 当前已成交部分的利润
    @property
    def profit(self):
        return self._profit

    @profit.setter
    def profit(self, value):
        self.__close_profit_list.append(value)
        self._profit += value

    # 对外暴露的是标准的滑点，即以点为单位的整数
    @property
    def slippage(self):
        return self._slippage / Order.slippage_mapper[self._symbol]

    @property
    def strategy_id(self):
        return self._strategy_id

    @property
    def remained_value(self):
        return self._remained_value

    def refresh_remained_value_by_price(self, price):
        """
        刷新订单未平仓部分的当前价值
        Parameters
        ----------
        price: 当前市场价格
        """
        if self._type == ORDER_BUY:
            self._remained_value = (price - self._slippage) * self._remained_volume
        else:
            self._remained_value = -(price + self._slippage) * self._remained_volume
        return self._remained_value

    def get_close_profit_list(self):
        return self.__close_profit_list

    def get_close_time_list(self):
        return self.__close_time_list

    def trade(self, lots, dt):
        """
        订单。
        :param lots: 手数，应该小于等于当前未成交手数。
        :param dt: 平仓时间。
        :return: 订单状态
        """
        # 传入的volume应该小于等于当前未成交volume
        volume = round(lots, 0.01) * Order.volume_mapper[self._symbol]
        assert self._volume - self._traded_volume - volume >= 0.0

        self._traded_volume += volume
        self._remained_volume = self._volume - self._traded_volume

        if abs(self._remained_volume) <= FLOAT_PRECISION_TOLERANCE:  # trade_volume == volume，即该单已平掉
            self._state = ORDER_STATE_CLOSED
        else:
            self._state = ORDER_STATE_IN_POSITION

        self.__close_time_list.append(dt)  # 增加平仓时间
        return self._state

    def cancel(self):
        """
        取消订单。
        :return:
        """
        self._state = ORDER_STATE_CANCELLED

    def execute(self, dt):
        """
        以该订单开仓或加仓。
        :dt:时间。开单成功的时间
        :price:当前的成交价
        :return:
        """
        self._order_time = dt
        self._state = ORDER_STATE_IN_POSITION


class CloseOrder(OrderBase):
    """
    平仓订单
    """
    ORDERCOUNT = 0

    def __init__(self, symbol, order_type, price, lots, slippage, dt, target_order_id):
        self._order_id = 'CloseOrder' + str(CloseOrder.ORDERCOUNT)  # 订单编号
        CloseOrder.ORDERCOUNT += 1
        self._symbol = symbol  # 合约代码
        self._type = order_type  # 报单方向
        self._price = float(price)  # 报单价格
        self._lots = lots  # 下单手数
        self._volume = round(lots, 0.01) * CloseOrder.volume_mapper[symbol]  # 报单总数量
        self._slippage = slippage * CloseOrder.slippage_mapper[symbol]  # 滑点
        if self._type == ORDER_BUY:
            self._price_with_slippage = self._price + self._slippage
        else:
            self._price_with_slippage = self._price - self.slippage
        self._cost = self._price_with_slippage * self._volume
        self._profit = 0  # 该单平完仓后的利润
        self._target_order_id = target_order_id
        self._order_time = dt  # 发单时间
        self._state = ORDER_STATE_PENDING  # 订单状态

    @property
    def order_id(self):
        return self._order_id

    @property
    def state(self):
        return self._state

    # 对外暴露的是加上滑点后的真实价格
    @property
    def price(self):
        return self._price_with_slippage

    # 下单手数
    @property
    def lots(self):
        return self._lots

    # 下单成本
    @property
    def cost(self):
        return self._cost

    @property
    def symbol(self):
        return self._symbol

    # 买还是卖
    @property
    def type(self):
        return self._type

    @property
    def order_time(self):
        return self._order_time

    # 平仓后的利润
    @property
    def profit(self):
        return self._profit

    # 对外暴露的是标准的滑点，即以点为单位的整数
    @property
    def slippage(self):
        return self._slippage / CloseOrder.slippage_mapper[self._symbol]

    @property
    def target_order_id(self):
        return self._target_order_id

    @profit.setter
    def profit(self, value):
        self._profit = value

    def execute(self, dt):
        """
        因为是关闭订单，该单只会成交一次。
        修改该单的价格为真实的成交价格。
        Parameters
        ----------
        price： 当前的市场价。
        """
        self._state = ORDER_STATE_CLOSED
        self._order_time = dt

    def calculate_profit(self, target_order):
        """
        计算平仓收益
        :return: 平仓收益
        """
        cost1 = target_order.price * self._volume
        cost2 = self.price * self._volume
        if target_order.type == ORDER_BUY:
            return cost2 - cost1
        else:
            return cost1 - cost2


class Position(object):
    """
    仓位
    """

    def __init__(self, symbols):
        self.__position_dict = {}
        for s in symbols:
            self.__position_dict[s] = []

    def open_position(self, order, symbol, dt):
        """
        建仓或加仓。
        :param order: 订单
        :param symbol: 品种代码
        :param dt: 当前时间
        :price: 开仓价格
        """
        if order not in self.__position_dict[symbol]:
            order.execute(dt)
            self.__position_dict[symbol].append(order)

    def close_position(self, order1, order2, lots, dt):
        """
        减仓或平仓。
        :param order1: 待平仓订单
        :param order2:
        :param lots: 要平的手数
        :param dt: 平仓时间
        :return: 关闭的订单状态
        """
        # 刷新order2的信息
        order2.execute(dt)  # 执行closeorder

        # 计算这两个order的平仓收益
        pf = order2.calculate_profit(order1)
        order1.profit = pf
        order2.profit = pf

        # 关闭order1
        lots = min(lots, order1.lots_remaining)
        order1.trade(lots, dt)
        if order1.state == ORDER_STATE_CLOSED:
            self.__position_dict[order1.symbol].remove(order1)

    def get_orders(self, symbol):
        """
        获取所有的未平的订单
        :param symbol: 品种
        :return:
        """
        return self.__position_dict[symbol]

    def has_order(self, order):
        symbol = order.symbol
        return order in self.get_orders(symbol)

    def cancel_order(self, order):
        order.cancel()
        self.__position_dict[order.symbol].remove(order)


class Account(object):
    """
    账户类
    """
    def __init__(self, engine, position, balance, leverage):
        self.__engine = engine
        self.__position = position
        self.__initial_balance = balance
        self.__balance = balance
        self.__leverage = leverage
        self.__margin = 0
        self.__free_margin = self.__balance
        self.__position_equity = 0
        self.__nonposition_equity = self.__balance

    @property
    def balance(self):
        return self.__balance

    @property
    def equity(self):
        return self.__nonposition_equity + self.__position_equity

    @property
    def free_margin(self):
        return self.__free_margin

    @property
    def margin(self):
        return self.__margin

    def is_cost_in_margin(self, cost):
        """
        某个成本为cost的订单是否可以下单。
        :param cost: 下单成本。
        :return:
        """
        return cost / self.__leverage >= self.__free_margin

    def refresh_by_close(self, order):
        """
        平单后刷新帐户
        :param order: 平仓订单CloseOrder
        :return:
        """
        target_order = self.__engine.get_order_by_orderid(order.target_order_id)  # 被平掉的订单
        total_lots_target_order = target_order.lots
        ratio = order.lots / total_lots_target_order
        self.__margin -= target_order.cost / self.__leverage * ratio
        if target_order.type == ORDER_BUY:
            self.__nonposition_equity += ratio * target_order.cost + order.profit
        else:
            self.__nonposition_equity -= ratio * target_order.cost - order.profit
        self.refresh_by_data()
        self.__balance += order.profit

    def refresh_by_open(self, order):
        """
        开单后刷新帐户
        :param order: 订单
        :return:
        """
        self.__margin += order.cost / self.__leverage
        if order.type == ORDER_BUY:
            cost = order.cost
        else:
            cost = -order.cost
        self.__nonposition_equity -= cost
        self.refresh_by_data()

    def refresh_by_data(self):
        """
        市场行情的变化导致equity的变化，刷新equity的值
        同时也导致可用保证金free_margin的变化
        :return: 刷新后的equity值和free_margin值
        """
        self.__position_equity = 0
        current_data = self.__engine.current_data

        for sym in self.__engine.symbols:
            for order in self.__position.get_orders(sym):
                if self.__engine.mode == BACK_TEST_MODE_ONBAR:
                    price = current_data[sym][FOREX_CLOSE_B]
                else:
                    price = (current_data[sym][1] + current_data[sym][0]) / 2.0
                self.__position_equity += order.refresh_remained_value_by_price(price)            # 刷新每个order的当前未平仓部分的价值

        equity = self.__nonposition_equity + self.__position_equity
        self.__free_margin = equity - self.__margin
        if equity < self.__initial_balance:
            raise ACCOUNT_LOSE
        return equity, self.__free_margin


class BackTestEngine(object):

    def __init__(self, backtest, start, end, symbols, mode, time_step, market_type, balance, leverage):
        self.__dg = DataGenerator(self, start, end, symbols, mode, time_step, market_type)
        self.__back_test = backtest
        self.__date_time = None
        self.__mode = mode
        self.__current_data = {}
        self.__symbols = symbols

        self.__order_dict = OrderedDict()
        self.__pending_order_dict = {}

        self.__position = Position(self.__symbols)
        self.__account = Account(self, self.__position, balance, leverage)

        self.__data_counter = 0
        self.__buffer_handler = BufferHandler(time_step)

        self.__event_handler = EventProcessor()

    @property
    def symbols(self):
        return self.__symbols

    @property
    def current_data(self):
        return self.__current_data

    @property
    def mode(self):
        return self.__mode

    def get_event_handler(self):
        return self.__event_handler

    def __refresh_current_data(self, data):
        """
        更新最新的数据
        :param data: onbar为tuple，ontick为list
        :return:
        """
        if self.__mode == BACK_TEST_MODE_ONBAR:      # onbar
            for item in data:
                self.__current_data[item[FOREX_SYMBOL]] = item
        elif self.__mode == BACK_TEST_MODE_ONTICK:        # ontick
            self.__current_data[data[3]] = data
        else:
            raise TypeError(str(BACK_TEST_ENGINE_TYPE_ERROR))
        self.__data_counter += 1

    def add_buffers(self, symbol, data_buffer, buffer_name, period):
        """
        添加数据数组
        :param symbol: 产品代码
        :param period: 周期
        :param buffer_name: 名称，比如BUFFER_CLOSE
        :param data_buffer: 数组
        :return:
        """
        self.__buffer_handler.add_buffers(symbol, period, buffer_name, data_buffer)

    def run(self):
        self.__dg.push_data()

    def stop(self):
        self.__dg.stop()

    def __set_buffers(self, key, date_time, open, high, low, close, volume):
        """
        更新key的所有的周期的buffer
        :param key: symbol，产品代码
        :param date_time: 时间
        :param open:
        :param high:
        :param low:
        :param close:
        :param volume:
        :return:
        """
        self.__buffer_handler.set_buffers(key, date_time, open, high, low, close, volume)

    def on_bar(self, tp):
        """
        :param tp: 一个元组，每个元素为一个dict对象（包括date_time open close high low volume symbol）
        """
        self.__date_time = tp[0].get(FOREX_DATETIME_B, None)
        for item in tp:
            self.__set_buffers(item[FOREX_SYMBOL], item[FOREX_DATETIME_B], item[FOREX_OPEN_B],
                               item[FOREX_HIGH_B], item[FOREX_LOW_B], item[FOREX_CLOSE_B], item[FOREX_VOLUME_B])
        self.__processing(tp)
        self.__back_test.on_bar(date_time=datetime.strptime(self.__date_time, FOREX_TIME_FOMAT))
        self.__cross_order()

    def on_tick(self, arr):
        """
        :param arr: 一个长度为4的list(ask, bid，servertime，symbol)
        """
        self.__date_time = arr[2]
        self.__set_buffers(arr[3], arr[2], (arr[0]+arr[1])/2.0, arr[0], arr[1], (arr[0]+arr[1])/2.0, 100)
        self.__processing(arr)
        # self.__back_test.on_tick(ask=arr[0], bid=arr[1], symbol=arr[3],
        #                          date_time=datetime.strptime(self.__date_time, FOREX_TIME_FOMAT))
        self.__cross_order()

    def __processing(self, current_data):
        """
        onbar和ontick的共有的数据处理模块，包括刷新当前数据，撮合订单，更新账户情况等。
        Parameters
        ----------
        current_data: 当前数据。

        Returns
        -------
        None
        """
        self.__refresh_current_data(current_data)
        self.__refresh_account()

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
        if order.order_id in self.__pending_order_dict.keys():
            del self.__pending_order_dict[order.order_id]
            order.cancel()
        if self.__position.has_order(order):
            self.__position.cancel_order(order)
        return order.state

    def send_order(self, symbol, price, volume, order_type, slippage, strategy_id):
        """
        symbol: 合约代码
        price: 价格
        volume: 手数
        order_type: 订单类型
        slippage: 滑点
        strategy_id: 下单的策略编号
        Returns
        -------
        order id.
        """
        order = Order(symbol, order_type, price, volume, slippage, self.__date_time, strategy_id)
        self.__order_dict[order.order_id] = order
        self.__pending_order_dict[order.order_id] = order
        return order.order_id

    def close_order(self, order, order_price, lots):
        """
        关闭指定订单
        :param order:
        :param lots: 指定手数
        :param order_price: 平仓价格
        :return: order状态
        """
        assert order.state == ORDER_STATE_IN_POSITION
        lots = min(lots, order.lots_remaining)

        if order.type == ORDER_BUY:
            order_type = ORDER_SELL
            # if self.__mode == BACK_TEST_MODE_ONBAR:               # 当前为onbar模式
            #     order_price = self.__current_data[order.symbol][FOREX_OPEN_B]
            # else:                                              # 当前为ontick模式
            #     order_price = self.__current_data[order.symbol][1]
        else:
            order_type = ORDER_BUY
            # if self.__mode == BACK_TEST_MODE_ONBAR:
            #     order_price = self.__current_data[order.symbol][FOREX_OPEN_B]
            # else:
            #     order_price = self.__current_data[order.symbol][0]
        
        close_order = CloseOrder(order.symbol, order_type, order_price, lots, order.slippage, self.__date_time, order.order_id)

        self.__order_dict[close_order.order_id] = close_order
        self.__pending_order_dict[close_order.order_id] = close_order
        return ORDER_STATE_PENDING

    def get_data(self, symbol, period, buffer_name):
        """
        获取数据数组
        :param symbol: 产品代码
        :param period: 周期
        :param buffer_name: 数据类型名称
        :return:
        """
        return self.__buffer_handler.get_data(symbol, period, buffer_name)

    def __check_account_stable(self, order):
        """
        检查账户资金是否足够开单
        :param order: 待开订单
        :return: boolean
        """
        if self.__account.is_cost_in_margin(order.cost):
            return True
        return False

    def __cross_order(self):
        """
        撮合交易，并更新仓位账户等信息。
        :return:
        """
        for i, order in self.__pending_order_dict.items():
            if not self.__check_account_stable(order):
                continue

            if isinstance(order, CloseOrder):
                order_id = self.__cross_close_order(order)  # 平仓后仓位将发生变化
                if order_id != CROSS_ORDER_FAILED:
                    del self.__pending_order_dict[order_id]
                    self.__account.refresh_by_close(order)
            else:
                order_id = self.__cross_open_order(order)   # 开仓后仓位将发生变化
                if order_id != CROSS_ORDER_FAILED:              # 若撮合交易成功
                    del self.__pending_order_dict[order_id]       # 从pending list 中删除
                    self.__account.refresh_by_open(order)

    def __refresh_account(self):
        """
        刷新账户价值
        :return:
        """
        self.__account.refresh_by_data()

    def __is_order_acceptable(self, order):
        """
        判断当前order是否能开单。
        :param order:
        :return: boolean
        """
        accept = False
        symbol = order.symbol

        # 若交易量太大，应该拆分成几单来下
        # 若交易量甚至大于当前tick或bar的总量，则应该分笔下单
        # 暂不实现该功能，因为实现时有较多细节需要考虑，而且tick数据也还没有volume字段。
        # 默认所下的单的volume都远小于市场订单总volume。
        # if self.__mode == BACK_TEST_MODE_ONBAR:
        #     if order.volume > self.__current_data[symbol][FOREX_VOLUME_B]:
        #         return

        if order.type == ORDER_BUY:
            if self.__mode == BACK_TEST_MODE_ONBAR:
                if order.price >= self.__current_data[symbol][FOREX_LOW_B]:
                    accept = True
            else:
                if order.price >= self.__current_data[symbol][0]:
                    accept = True
        else:
            if self.__mode == BACK_TEST_MODE_ONBAR:
                if order.price <= self.__current_data[symbol][FOREX_HIGH_B]:
                    accept = True
            else:
                if order.price <= self.__current_data[symbol][1]:
                    accept = True
        return accept

    def __cross_open_order(self, order):
        """
        判断是否可以成交开仓，若可以则更新仓位。
        :param order: 交易的订单
        :return: 成功则返回订单编号，失败返回交易失败常量：CROSS_ORDER_FAILED
        """
        accept = self.__is_order_acceptable(order)
        if not accept:
            return CROSS_ORDER_FAILED

        self.__position.open_position(order, order.symbol, self.__date_time)
        return order.order_id

    def __cross_close_order(self, order):
        """
        判断是否可以成交平仓，若可以则更新仓位。
        :param order: 交易的平仓订单
        :return: 成功则返回订单编号，失败返回交易失败常量：CROSS_ORDER_FAILED
        """
        accept = self.__is_order_acceptable(order)
        if not accept:
            return CROSS_ORDER_FAILED

        target_id = order.target_order_id
        lots = order.lots

        for od in self.__position.get_orders(order.symbol):
            if od.order_id == target_id:
                self.__position.close_position(od, order, lots, self.__date_time)        # 关闭订单
                return order.order_id

        return CROSS_ORDER_FAILED

    def get_position_orders(self, symbol):
        return self.__position.get_orders(symbol)

    def get_equity(self):
        return self.__account.equity

    def get_history_orders_by_symbol(self, symbol):
        return [od[1] for od in self.__order_dict.iteritems() if (od[1].symbol == symbol and not isinstance(od[1], CloseOrder))]

    def get_history_order_by_strategyid(self, strategy_id):
        return [od[1] for od in self.__order_dict.iteritems() if (od[1].strategy_id == strategy_id and not isinstance(od[1], CloseOrder))]

    def get_pending_orders(self):
        return [od[1] for od in self.__pending_order_dict.iteritems() if not isinstance(od[1], CloseOrder)]

    def get_cancelled_orders(self):
        return [od[1] for od in self.__order_dict.iteritems() if not isinstance(od[1], CloseOrder) and od[1].state == ORDER_STATE_CANCELLED]

    def get_closed_orders(self):
        return [od[1] for od in self.__order_dict.iteritems() if not isinstance(od[1], CloseOrder) and od[1].state == ORDER_STATE_CLOSED]

    def get_history_orders(self):
        return [od[1] for od in self.__order_dict.iteritems() if not isinstance(od[1], CloseOrder)]

    def get_history_effective_orders(self):
        """
        历史中已平仓订单和在仓位中的订单
        """
        return [od[1] for od in self.__order_dict.iteritems() if
                not isinstance(od[1], CloseOrder) and (od[1].state == ORDER_STATE_CLOSED or od[1].state == ORDER_STATE_IN_POSITION)]

    def get_order_by_orderid(self, id):
        return self.__order_dict[id]


class BufferHandler(object):
    """
    数组操控者
    """
    def __init__(self, time_step):
        self.data_buffers = {}
        self.time_step = time_step
        self.last_bar_recorder = {}

        self.__1mindelta = timedelta(minutes=1)
        self.__5mindelta = timedelta(minutes=5)
        self.__15mindelta = timedelta(minutes=15)
        self.__1hourdelta = timedelta(hours=1)
        self.__4hourdelta = timedelta(hours=4)
        self.__1daydelta = timedelta(days=1)
        self.__1weekdelta = timedelta(days=5)
        self.time_minute_mapper = {TIME_STEP_1MINUTE: self.__1mindelta, TIME_STEP_5MINUTE: self.__5mindelta,
                                   TIME_STEP_15MINUTE: self.__15mindelta, TIME_STEP_1HOUR: self.__1hourdelta,
                                   TIME_STEP_4HOUR: self.__4hourdelta, TIME_STEP_1DAY: self.__1daydelta,
                                   TIME_STEP_1WEEK: self.__1weekdelta}

    def add_buffers(self, symbol, period, buffer_name, data_buffer):
        """
        添加数据数组
        :param symbol: 产品代码
        :param period: 周期
        :param buffer_name: 名称，比如BUFFER_CLOSE
        :param data_buffer: 数组
        :return:
        """
        if self.data_buffers.get(symbol) is None:
            self.data_buffers[symbol] = {period: {buffer_name: data_buffer}}
        else:
            if self.data_buffers[symbol].get(period) is None:
                self.data_buffers[symbol][period] = {buffer_name: data_buffer}
            else:
                if self.data_buffers[symbol][period].get(buffer_name) is not None:
                    raise ValueError(BUFFER_ALLOCATION_FAILURE)
                self.data_buffers[symbol][period][buffer_name] = data_buffer

        self.last_bar_recorder[symbol] = {TIME_STEP_1MINUTE: datetime(1900, 1, 1), TIME_STEP_5MINUTE: datetime(1900, 1, 1),
                                          TIME_STEP_15MINUTE: datetime(1900, 1, 1), TIME_STEP_1HOUR: datetime(1900, 1, 1),
                                          TIME_STEP_4HOUR: datetime(1900, 1, 1), TIME_STEP_1DAY: datetime(1900, 1, 1),
                                          TIME_STEP_1WEEK: datetime(1900, 1, 1)}

    def get_data(self, symbol, period, buffer_name):
        """
        传入产品代码，周期，‘OHLCVT’之一获取对应的数组，前提是回测前分配过该数组，否则抛出异常。
        :param symbol:
        :param period:
        :param buffer_name:
        :return:
        """
        try:
            return self.data_buffers[symbol][period][buffer_name]
        except KeyError:
            print symbol + ' time step: ' + str(period) + ' ' + buffer_name
            print BUFFER_NOT_ALLOCATED
            f = sys.exc_info()[2].tb_frame.f_back
            print COMMON_ERROR_POSITION.format(f.f_code.co_filename, f.f_code.co_name, f.f_lineno)
            exit(-1)

    def set_buffers(self, symbol, date_time, open, high, low, close, volume):
        """
        用新传入的数据刷新数组
        :param symbol: 产品代码
        :param date_time: 时间戳
        :param open:
        :param high:
        :param low:
        :param close:
        :param volume:
        :return:
        """
        # 秒数归零
        date_time = date_time[:-2] + '00'
        date_time = datetime.strptime(date_time, FOREX_TIME_FOMAT)

        if symbol not in self.data_buffers.keys():
            return

        for period in self.data_buffers[symbol].keys():
            if date_time - self.last_bar_recorder[symbol][period] >= self.time_minute_mapper[period]:
                self.last_bar_recorder[symbol][period] = date_time

                if BUFFER_OPEN in self.data_buffers[symbol][period].keys():
                    self.data_buffers[symbol][period][BUFFER_OPEN].push_back(open)
                if BUFFER_CLOSE in self.data_buffers[symbol][period].keys():
                    self.data_buffers[symbol][period][BUFFER_CLOSE].push_back(close)
                if BUFFER_HIGH in self.data_buffers[symbol][period].keys():
                    self.data_buffers[symbol][period][BUFFER_HIGH].push_back(high)
                if BUFFER_LOW in self.data_buffers[symbol][period].keys():
                    self.data_buffers[symbol][period][BUFFER_LOW].push_back(low)
                if BUFFER_VOLUME in self.data_buffers[symbol][period].keys():
                    self.data_buffers[symbol][period][BUFFER_VOLUME].push_back(volume)
                if BUFFER_TIME in self.data_buffers[symbol][period].keys():
                    self.data_buffers[symbol][period][BUFFER_TIME].push_back(date_time)

            else:
                if BUFFER_HIGH in self.data_buffers[symbol][period].keys():
                    if high > self.data_buffers[symbol][period][BUFFER_HIGH][0]:
                        self.data_buffers[symbol][period][BUFFER_HIGH][0] = high
                if BUFFER_LOW in self.data_buffers[symbol][period].keys():
                    if low < self.data_buffers[symbol][period][BUFFER_LOW][0]:
                        self.data_buffers[symbol][period][BUFFER_LOW][0] = low
                if BUFFER_CLOSE in self.data_buffers[symbol][period].keys():
                    self.data_buffers[symbol][period][BUFFER_CLOSE][0] = close
                if BUFFER_VOLUME in self.data_buffers[symbol][period].keys():
                    self.data_buffers[symbol][period][BUFFER_VOLUME][0] += volume


if __name__ == "__main__":
    pass
