# coding=utf-8

import numpy as np
from Queue import deque
# from ..core.common import *
REVERSED_INDEXING = 1
NORMAL_INDEXING = 2

class FixedBuffer(object):
    """
    a[id]得到第id个元素
    a[id]=b 设置第id个元素值为b
    仅支持简单的切片操作：
    a[x:y:z]获取x至y的区间的元素，但z只能为None。不允许设置为其他的值。
    内部包含一个定长的循环队列。新加入的元素覆盖最早的元素。
    """

    def __init__(self, length, mode=REVERSED_INDEXING):
        """
        :param length: 数组大小
        :param mode: 顺序或者逆序
        """
        assert length >= 1
        self.__length = length
        self.__array = np.asarray([None] * self.__length)
        self.__index = self.__length - 1
        self.__mode = mode
        self.__iter_counter = self.__index
        self.__iter_started = False

    def push_back(self, x):
        """
        设置最新的元素值为x
        顺序模式下为最后一个元素
        逆序模式下为最前面一个元素
        :param x:
        :return:
        """
        self.__index += 1
        self.__index %= self.__length
        self.__array[self.__index] = x

    def __str__(self):
        if self.__mode == NORMAL_INDEXING:
            t1 = ['{:.5f}'.format(x) for x in self.__array[(self.__index + 1) % self.__length:] if x is not None]
            t2 = ['{:.5f}'.format(x) for x in self.__array[: (self.__index + 1) % self.__length] if x is not None]
            t1 = np.hstack((t1, t2))
        else:
            t1 = ['{:.5f}'.format(x) for x in self.__array[self.__index:: -1] if x is not None]
            t2 = ['{:.5f}'.format(x) for x in self.__array[: self.__index: -1] if x is not None]
            t1 = np.hstack((t1, t2))
        return '  '.join(t1)

    def __len__(self):
        return self.__length

    def __getitem__(self, item):
        if self.__mode == REVERSED_INDEXING:
            return self.__get_reversed(item)
        else:
            return self.__get_normal(item)

    def __setitem__(self, key, value):
        if self.__mode == REVERSED_INDEXING:
            return self.__set_reversed(key, value)
        else:
            return self.__set_normal(key, value)

    def __get_normal(self, item):
        """
        顺序索引模式下得到item元素或item区间切片
        :param item: 索引
        :return:
        """
        if isinstance(item, int):
            if 0 <= item < self.__length:
                pointer = (self.__index + 1) % self.__length
                pointer = (pointer + item) % self.__length
                return self.__array[pointer]
            else:
                raise IndexError(BUFFER_INDEX_ERROR)
        if isinstance(item, slice):
            if item.step is not None:
                raise IndexError(BUFFER_INDEX_ERROR)
            if item.start is None and item.stop is None:
                part1 = self.__array[(self.__index + 1) % self.__length:]
                part2 = self.__array[: (self.__index + 1) % self.__length]
                part1 = np.hstack((part1, part2))
                return part1
            if item.start is None:
                start = (self.__index + 1) % self.__length
                if item.stop < 0 or item.stop >= self.__length:
                    raise IndexError(BUFFER_INDEX_ERROR)
                stop = (self.__index + 1) % self.__length
                stop = (item.stop + stop) % self.__length
                if start > stop:
                    part1 = self.__array[start:]
                    part2 = self.__array[: stop]
                    part1 = np.hstack((part1, part2))
                else:
                    part1 = self.__array[start: stop]
                return part1
            if item.stop is None:
                stop = (self.__index + 1) % self.__length
                if item.start >= self.__length or item.start < 0:
                    raise IndexError(BUFFER_INDEX_ERROR)
                start = (self.__index + 1) % self.__length
                start = (start + item.start) % self.__length
                if start >= stop:
                    part1 = self.__array[start:]
                    part2 = self.__array[: stop]
                    part1 = np.hstack((part1, part2))
                else:
                    part1 = self.__array[start: stop]
                return part1
            else:
                if 0 <= item.start <= item.stop < self.__length:
                    begin = (self.__index + 1) % self.__length
                    start = (begin + item.start) % self.__length
                    stop = (begin + item.stop) % self.__length
                    if start <= stop:
                        part1 = self.__array[start: stop]
                    else:
                        part1 = self.__array[start:]
                        part2 = self.__array[: stop]
                        part1 = np.hstack((part1, part2))
                    return part1
                else:
                    raise IndexError(BUFFER_INDEX_ERROR)
        else:
            raise IndexError(BUFFER_INDEX_ERROR)

    def __get_reversed(self, item):
        """
        逆序索引模式下得到item元素或item区间切片
        :param item: 索引
        :return:
        """
        if isinstance(item, int):
            if 0 <= item < self.__length:
                item = self.__length - item - 1
                return self.__get_normal(item)
            else:
                raise IndexError(BUFFER_INDEX_ERROR)
        if isinstance(item, slice):
            if item.step is not None:
                raise IndexError(BUFFER_INDEX_ERROR)
            if item.start is None and item.stop is None:
                res = self.__get_normal(item)
                return res[::-1]
            if item.start is None:
                if item.stop == 0:
                    return np.asarray([])
                if 0 < item.stop < self.__length:
                    stop = self.__length - item.stop
                else:
                    raise IndexError(BUFFER_INDEX_ERROR)
                res = self.__get_normal(slice(stop, None, None))
                return res[::-1]
            if item.stop is None:
                if item.start == 0:
                    start = None
                elif 0 < item.start < self.__length:
                    start = self.__length - item.start
                else:
                    raise IndexError(BUFFER_INDEX_ERROR)
                res = self.__get_normal(slice(None, start, None))
                return res[::-1]
            else:
                if not 0 <= item.start <= item.stop < self.__length:
                    raise IndexError(BUFFER_INDEX_ERROR)
                if item.start == item.stop:
                    return np.asarray([])
                elif item.start == 0:
                    start = None
                else:
                    start = self.__length - item.start
                stop = self.__length - item.stop
                res = self.__get_normal(slice(stop, start, None))
                return res[::-1]
        else:
            raise IndexError(BUFFER_INDEX_ERROR)

    def __set_normal(self, k, v):
        """
        顺序索引模式下设置下标为k的元素的值为v
        :param k: 下标索引
        :param v: 值
        :return:
        """
        if not 0 <= k < self.__length:
            raise IndexError(BUFFER_INDEX_ERROR)
        pointer = (self.__index + 1) % self.__length
        pointer = (pointer + k) % self.__length
        self.__array[pointer] = v

    def __set_reversed(self, k, v):
        """
        逆序索引模式下设置下标为k的元素的值为v
        :param k: 下标索引
        :param v: 值
        :return:
        """
        self.__set_normal(self.__length - k - 1, v)

    def __iter__(self):
        if self.__mode == NORMAL_INDEXING:
            self.__iter_counter = (self.__index + 1) % self.__length
            return self
        else:
            self.__iter_counter = self.__index
            return self

    def next(self):
        if self.__mode == NORMAL_INDEXING:
            if self.__iter_counter != (self.__index + 1) % self.__length or not self.__iter_started:
                res = self.__array[self.__iter_counter]
                self.__iter_counter = (self.__iter_counter + 1) % self.__length
                self.__iter_started = True
                return res
            else:
                self.__iter_started = False
                raise StopIteration
        else:
            if self.__iter_counter != self.__index or not self.__iter_started:
                res = self.__array[self.__iter_counter]
                self.__iter_counter = (self.__iter_counter - 1) % self.__length
                self.__iter_started = True
                return res
            else:
                self.__iter_started = False
                raise StopIteration
            
if __name__=="__main__":
    test=FixedBuffer(1000)
    for i in xrange(1000):
        test.push_back(i)
    

