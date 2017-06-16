# coding=utf-8
import sys
import time
from datetime import datetime

import numpy as np
from Backtest.backtest.core.BackTestBase import BackTestBase
from Backtest.backtest.core.common import *


class MutiBias(BackTestBase):
    """组合乖离策略"""

    def __init__(self,
                 start,
                 end,
                 symbols,
                 mode=BACK_TEST_MODE_ONBAR,
                 time_step=TIME_STEP_1MINUTE,
                 market_type=MARKET_TYPE_FOREX,
                 balance=1000000,
                 eventhandler_enabled=False,
                 avg=[24, -0.35, 0.50, 0.19, -0.03]):
        # 继承BackTestBase类
        super(MutiBias, self).__init__(start, end, symbols, mode, time_step, market_type, balance, eventhandler_enabled)
        # 分配数据内存空间		
        for symb in self.symbols:				
            self.allocate_data_buffers(symb, TIME_STEP_1MINUTE, 'CTO', 100)

        # 分配指标缓存空间	
        self.allocate_indicator_buffers('ma24', 100 , REVERSED_INDEXING)	
        self.allocate_indicator_buffers('bias24', 100 , REVERSED_INDEXING)		
        # 策略参数
        self.Ma_period = avg[0]  	 # ma周期
        self.LongInLevel = avg[1]	 # 当乖离值小于于该值，做多进场
        self.ShortInLevel = avg[2]   # 当乖离值大于该值，做空进场
        self.LongOutLevel = avg[3]   # 当乖离值大于该值，多单出场
        self.ShortOutLevel = avg[4]  # 当乖离值小于该值，空单出场
    # 在此定义类内全局变量
        self.magic_number = 20161117 # 标识策略ID
        self.lot = 0.1
        self.slippage = 0.55
        self.current_ma = 0.0
        self.last_ma = 0.0
        self.last_bias = 0.0
        self.order_profit = 0.0      # 当前订单的账面盈亏
        self.IsCheckOutTime = False
        
    def on_bar(self, date_time):
        """
        回测主程序，具体流程如下：
        1）使用get_data获取当前品种的收盘价等数据，要求预先已经分配好相应的缓存空间
        2) 计算策略所需指标
        3）判断目前是否有持仓,若有持仓则检查是否可以平仓，否则检查是否可以开仓
        """		
        for symb in self.symbols:
            
            # 获取当前品种的收盘价等数据	
            closebuf = self.get_data(symb, TIME_STEP_1MINUTE, BUFFER_CLOSE)
            openbuf = self.get_data(symb, TIME_STEP_1MINUTE, BUFFER_OPEN)
            timebuf = self.get_data(symb, TIME_STEP_1MINUTE, BUFFER_TIME)
            # 数据Bar数少于ma周期时，返回			
            if closebuf[self.Ma_period] is None:
                return
            
            # 计算当前的移动平均和乖离值	
            self.indicator_buffers['ma24'].push_back(np.mean(closebuf[:self.Ma_period]))
            self.indicator_buffers['bias24'].push_back((closebuf[0]-self.indicator_buffers['ma24'][0])*
                                                       100/self.indicator_buffers['ma24'][0])
            self.current_ma = self.indicator_buffers['ma24'][0]
            self.last_ma = self.indicator_buffers['ma24'][self.Ma_period]
            self.last_bias = self.indicator_buffers['bias24'][1]
            if self.last_bias is None or self.last_ma is None:
                return
            
            # 判断目前是否有持仓,若有持仓则检查是否可以平仓，否则检查是否可以开仓
            current_order = self.get_orders(symb)
            if current_order:
                # 计算是否平仓，并返回开仓类型
                order_close_type = self.check_for_close(closebuf, current_order)
                # 做多出场
                if order_close_type is ORDER_BUY:
                    self.close_order(current_order[0], openbuf[0], self.lot)
                # 做空出场
                if order_close_type is ORDER_SELL:
                    self.close_order(current_order[0], openbuf[0], self.lot)
            else:
                # 计算是否开仓，并返回开仓类型
                order_open_type = self.check_for_open()
                # 做多入场
                if order_open_type is ORDER_BUY:
                    self.send_order(self.magic_number, symb, openbuf[0], self.lot, ORDER_BUY, self.slippage)
                # 做空入场						
                if order_open_type is ORDER_SELL:
                    self.send_order(self.magic_number, symb,  openbuf[0], self.lot, ORDER_SELL, self.slippage)

    def on_tick(self, ask, bid, symbol,  date_time):
        pass

    def buy_condition(self):
        """做多进场条件"""		
        # BIAS小于LongInLevel进场
        if self.last_bias <= self.LongInLevel:
            return True
        else:
            return False

    def sell_condition(self):
        """做空进场条件"""
        # BIAS大于bias_short进场
        if self.last_bias >= self.ShortInLevel:
            return True
        else:
            return False  

    def buy_close_condition(self, pricebuf, current_order):
        """做多出场条件"""
        condition = self.current_ma-self.last_ma
        self.order_profit = pricebuf[1]-(current_order[0].price+current_order[0].slippage)
        # BIAS大于bias_sell进场且斜率小于0 或者 持仓时间超过一定阀值且盈利10美元以上      
        if (self.last_bias >= self.LongOutLevel and condition < 0.0) or (self.check_hold_time() and self.order_profit> 10.0):
            return True
        else:
            return False

    def sell_close_condition(self, pricebuf, current_order):
        """做空出场条件""" 
      
        condition = self.current_ma-self.last_ma
        self.order_profit = current_order[0].price-pricebuf[1]-current_order[0].slippage
        if (self.last_bias <= self.ShortOutLevel and condition > 0) or (self.check_hold_time() and self.order_profit > 10.0):
            return True
        else:
            return False        

    def check_for_open(self):
        """检查是否开仓"""
        res = " "
        # 若没有持仓
        if self.buy_condition():
            res = ORDER_BUY
        if self.sell_condition():
            res = ORDER_SELL

        return res
           
    def check_for_close(self, pricebuf, current_order):
        """检查是否平仓"""
        res = " "
        if current_order[0].type == ORDER_BUY and self.buy_close_condition(pricebuf, current_order):
            res = ORDER_BUY     
        elif current_order[0].type == ORDER_SELL and self.sell_close_condition(pricebuf, current_order):
            res = ORDER_SELL
        return res

    def cal_hold_time(self, start, end, time_unit='M'):
        """
        计算持仓的时间间隔
        Parameters
        ----------
        start:为回测开始日期，格式为 '2016-02-04 00:59:00'
        end:为回测结束日期，格式为 '2016-08-04 00:59:00'
        time_unit:时间单位为 'S','M','H','D'

        Returns
        -------
        hold_time:
        """
        # 计算日期字符串是星期几，0,1,2,3,4,5,6代表周一到周日
        start = start.replace('.', '-')
        end = end.replace('.', '-')
        __weekday_start = datetime.strptime(start, "%Y-%m-%d %H:%M").weekday()
        __weekday_end = datetime.strptime(end, "%Y-%m-%d %H:%M").weekday()
        # 计算两个日期的间隔描述
        __start = time.strptime(start, "%Y-%m-%d %H:%M")
        __end = time.strptime(end, "%Y-%m-%d %H:%M")
        seconds = time.mktime(__end) - time.mktime(__start)
        # 隔周六周日相当于减去2880秒
        if __weekday_end == 0 and __weekday_start == 4:
            _seconds = seconds - 2880 * 60

        if time_unit is 'M':
            hold_time = _seconds / 60
        elif time_unit is 'H':
            hold_time = _seconds / (60 * 60)
        elif time_unit is 'D':
            hold_time = _seconds / (60 * 60 * 24)
        else:
            hold_time = _seconds

        return hold_time

    def check_hold_time(self):
        """
         检查订单持仓时间，若持仓时间超过out_time则出场
         Open_date_str：开仓时间字符串
         trade_date：当前时间字符串
        """
        if self.IsCheckOutTime is False:
            return False
        if self.cal_hold_time(self.OrderInf["OpenTime"], self.trade_date) >= self.outTime:
            return True
        else: 
            return False    

if __name__ == "__main__":
    pass
