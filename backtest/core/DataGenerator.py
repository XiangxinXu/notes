# coding=utf-8

from datetime import timedelta
from threading import Thread
import Queue
import dateutil.parser
import pandas as pd
import pymongo

from ..core.common import *


class DataGenerator:
    """
    在回测中为策略提供数据。
    """

    def __init__(self,
                 back_test_strategy,                                 # 回测策略对象
                 start,                                              # 回测起始时间，任意的表示时间的字符串类型
                 end,                                                # 回测结束时间，任意的表示时间的字符串类型
                 symbols,                                            # 交易品种名
                 mode=BACK_TEST_MODE_ONBAR,                          # 回测模式，onBar或onTick
                 time_step=TIME_STEP_1MINUTE,           # 每个bar的时间跨度，仅对onBar模式有效
                 market_type=MARKET_TYPE_FOREX):                     # 市场类型（！目前仅支持外汇）

        self.back_test_strategy = back_test_strategy

        if isinstance(start, str) and isinstance(end, str):
            self.start = dateutil.parser.parse(start)
            self.end = dateutil.parser.parse(end)
        else:
            raise TypeError(str(DATAGENERATOR_START_END_TYPE_ERROR))
        if self.end <= self.start:
            raise ValueError(str(DATAGENERATOR_START_END_VALUE_ERROR))

        self.time_step = time_step
        self.bt_mode = mode
        self.market_type = market_type
        self._is_stop = False

        if not isinstance(symbols, set):
            raise ValueError(str(DATAGENERATOR_SYMBOL_TYPE_ERROR))

        self.__onbar_name_translation(mode, symbols, time_step)

        self.__connect_db()

        self.__1mindelta = timedelta(minutes=1)
        self.__5mindelta = timedelta(minutes=5)
        self.__15mindelta = timedelta(minutes=15)
        self.__1hourdelta = timedelta(hours=1)
        self.__4hourdelta = timedelta(hours=4)
        self.__1daydelta = timedelta(days=1)
        self.__1weekdelta = timedelta(days=5)

        self._data_fetcher = DataFetcher(self, self.start, self.end, self.symbols, self.db)  # 一个取数据的线程

    def __onbar_name_translation(self, mode, symbols, time_step):
        if mode == BACK_TEST_MODE_ONBAR:
            ts = BAR_1M
            new_symbols = set()
            if time_step == TIME_STEP_1MINUTE:
                ts = BAR_1M
            elif time_step == TIME_STEP_5MINUTE:
                ts = BAR_5M
            elif time_step == TIME_STEP_15MINUTE:
                ts = BAR_15M
            elif time_step == TIME_STEP_1HOUR:
                ts = BAR_1H
            elif time_step == TIME_STEP_4HOUR:
                ts = BAR_4H
            elif time_step == TIME_STEP_1DAY:
                ts = BAR_1D
            elif time_step == TIME_STEP_1WEEK:
                ts = BAR_1W
            for sym in symbols:
                new_symbols.add(sym + ts)
            self.symbols = new_symbols
        else:
            self.symbols = symbols

    def __connect_db(self):
        db_client = pymongo.MongoClient(MONGO_HOST_IP, MONGO_HOST_PORT)
        if self.market_type == MARKET_TYPE_FOREX:
            self.db = db_client[MONGO_FOREX]
        elif self.market_type == MARKET_TYPE_STOCK:
            pass
        elif self.market_type == MARKET_TYPE_FUTURE:
            pass
        elif self.market_type == MARKET_TYPE_OPTION:
            pass

    def __step_forward(self, date_time):
        """
        根据设定的步长向后推移时间
        Parameters
        ----------
        date_time 当前时间

        Returns
        -------
        推移后的时间
        """
        if self.time_step == TIME_STEP_1MINUTE:
            return date_time + self.__1mindelta
        elif self.time_step == TIME_STEP_5MINUTE:
            return date_time + self.__5mindelta
        elif self.time_step == TIME_STEP_15MINUTE:
            return date_time + self.__15mindelta
        elif self.time_step == TIME_STEP_1HOUR:
            return date_time + self.__1hourdelta
        elif self.time_step == TIME_STEP_4HOUR:
            return date_time + self.__4hourdelta
        elif self.time_step == TIME_STEP_1DAY:
            return date_time + self.__1daydelta
        elif self.time_step == TIME_STEP_1WEEK:
            return date_time + self.__1weekdelta
        else:
            return date_time + self.__1mindelta

    def __push_data_timer(self):
        """
        给策略发送OnBar数据。
        Returns
        -------

        """
        self._data_fetcher.start()
        while not self._is_stop:
            try:
                data = self._data_fetcher.get_data()
            except Queue.Empty:
                continue
            for d in data:
                self.back_test_strategy.on_bar(d)

        self._data_fetcher.stop()
        while 1:  # 跳出后将queue中元素取完后才通知data_fetcher停止，否则data_fetcher可能被阻塞而收不到停止通知。
            try:
                data = self._data_fetcher.get_data()
                for d in data:
                    self.back_test_strategy.on_bar(d)
            except Queue.Empty:
                break

    def __push_data_ticker(self):
        """
        给策略发送OnTick数据。
        Returns
        -------

        """
        collections = set()
        for sym in self.symbols:
            collections.add(self.db[sym])

        dt = self.start
        while dt < self.end and not self._is_stop:
            left_str = dt.strftime(FOREX_TIME_FOMAT)
            right = dt + timedelta(hours=4)

            if right > self.end:
                right = self.end
            right_str = right.strftime(FOREX_TIME_FOMAT)
            time_span = {FOREX_SERVERTIME_T: {'$gte': left_str, '$lt': right_str}}

            df = None
            for co in collections:
                cursor = co.find(time_span)
                if df is None:
                    df = pd.DataFrame(list(cursor))
                else:
                    df = pd.concat([df, pd.DataFrame(list(cursor))], ignore_index=True)

            if df is not None and len(df) > 0:
                del df[MONGO_ID]
                del df[FOREX_LOCALTIME_T]
                df.sort_values(by=FOREX_SERVERTIME_T, inplace=True)
                df.reset_index(inplace=True)
                [self.back_test_strategy.on_tick(
                                [float(row[2]),                 # FOREX_ASK_T
                                float(row[3]),                  # FOREX_BID_T
                                row[4],                         # FOREX_SERVERTIME_T
                                row[5]])                        # FOREX_SYMBOL_T
                 for row in df.itertuples()]

            dt = dt + timedelta(hours=4)

    def push_data(self):
        if self.bt_mode == BACK_TEST_MODE_ONBAR:
            self.__push_data_timer()
        else:
            self.__push_data_ticker()

    def stop(self):
        self._is_stop = True


class DataFetcher(Thread):

    def __init__(self, dg, left, right, symbols, db):
        super(DataFetcher, self).__init__()
        self.data_generator = dg
        self.queue = Queue.Queue(3)
        self.queue.join()
        self.__stop = False
        self.left = left
        self.right = right
        self.chunk_size = timedelta(days=10)
        self.symbols = symbols
        self.db = db

    def stop(self):
        self.__stop = True

    def run(self):
        dt = self.left
        while dt < self.right and not self.__stop:
            left_str = dt.strftime(FOREX_TIME_FOMAT)
            r = dt + self.chunk_size

            if r > self.right:
                r = self.right
            right_str = r.strftime(FOREX_TIME_FOMAT)
            time_span = {FOREX_DATETIME_B: {'$gte': left_str, '$lt': right_str}}

            cursor_list = []
            for sym in self.symbols:
                cursor = list(self.db[sym].find(time_span))
                if len(cursor) != 0:
                    map(lambda x: x.pop(MONGO_ID, ''), cursor)
                    cursor_list.append(cursor)
            data_list = zip(*cursor_list)
            while 1:
                try:
                    self.queue.put(data_list, block=False, timeout=3)
                    break
                except Queue.Full:
                    if self.__stop:
                        break
                    else:
                        continue
            if self.__stop:
                break
            dt = dt + self.chunk_size
        if self.__stop:
            return
        while not self.queue.empty():  # 直到data_generator取完数据才停止data_generator
            continue
        self.data_generator.stop()

    def get_data(self):
        return self.queue.get(block=False, timeout=3)
