# coding=utf-8

"""
EventProcessor（事件处理者）是一个处理事件的独立的线程。
如下情况可以考虑使用EP：
1、策略中涉及的较耗时的操作，如周期性地将数据写入外存，迭代地对实时数据通过模型进行优化和训练。
2、基于tick的策略中，当tick在短时间大量传入时，无法即时处理，可通过EP分散此刻的压力而不丢失数据。
   但策略至少要保证处理时间小于平均的tick间隔，即使如此，经过若干个tick的延迟，数据序列的价格也可能发生
   较大变化，可能会影响策略的效果。
3、其他类似的情况。
"""

import Queue
from collections import defaultdict, Iterable
from threading import Thread

from ..core.common import *


class EventProcessor(Thread):
    """事件进程"""
    def __init__(self):
        super(EventProcessor, self).__init__()
        self.__queue = Queue.Queue(EVENT_QUEUE_SIZE)
        self.__queue.join()
        self.__stop = False
        self.__processor = defaultdict(object)

    def stop(self):
        """停止线程"""
        while not self.__queue.empty():
            pass
        self.__stop = True

    def register_processor(self, **kwargs):
        """注册处理事件"""
        for key in kwargs:
            self.__processor[key] = kwargs[key]

    def unregister_processor(self, **kwargs):
        """注销处理事件"""
        for key in kwargs:
            del self.__processor[key]

    def on_event(self, **kwargs):
        """添加事件"""
        for event in kwargs:
            self.__queue.put(event, timeout=0.1)

    def run(self):
        """开始线程"""
        while not self.__stop:
            try:
                data = self.__queue.get(timeout=0.000001)
                self.__process_data(data)
            except Queue.Empty:
                pass

    def __process_data(self, data):
        """处理数据"""
        if isinstance(data[1], Iterable):
            self.__processor[data[0]](*data[1])
        else:
            self.__processor[data[0]](data[1])
