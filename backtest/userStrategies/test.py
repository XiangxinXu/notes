# #!/usr/bin/python
# # -*- coding: UTF-8 -*-
#
# import threading
# import time
# import pymongo
# import pandas as pd
#
# class MyThread (threading.Thread):   # 继承父类threading.Thread
#
#     def __init__(self):
#         threading.Thread.__init__(self)
#         self.handle = set()
#
#     def regester(self, handle):
#         if handle in self.handle:
#             return
#         self.handle.add(handle)
#
#     def run(self):                   # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
#         print "inside thread."
#         while 1:
#             for h in self.handle:
#                 h()
#
#
# class XXX:
#
#     def __init__(self):
#         self.thread = MyThread()
#         self.thread.regester(self.callback)
#
#     def callback(self):
#         time.sleep(5)
#         print "inside callback."
#
#     def always_run(self):
#         while 1:
#             print "in always run."
#             time.sleep(2.5)
#             pass
#
# if __name__ == "__main__":
#     dbClient = pymongo.MongoClient('192.168.0.158', 27017)
#     collection = dbClient['forex']['XAUUSD']
#     fd = {'servertime': {'$gte': '2016.10.03 01:01:01', '$lt': '2016.10.03 01:03:01'}}
#     print fd
#     initCursor = collection.find(fd)
#     print initCursor
#     print len(list(initCursor))
#     df = pd.DataFrame(list(initCursor))
#     print df
#
#
# def f(e, a, *args, **kwargs):
#     print e
#     print a
#     print '...'
#     for a in args:
#         print '1:', a
#     for a, b in kwargs.items():
#         print '2:', a, b


def enhanced(meth):
    def new(self, y):
        print "I am enhanced"
        return meth(self, y)
    return new


class C:
    @enhanced
    def bar(self, x):
        print "some method says:", x

c = C()
c.bar(1)
