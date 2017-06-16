# coding=utf-8

from PyQt4.QtGui import QStandardItem, QBrush, QColor
from PyQt4.QtCore import QVariant, Qt, QModelIndex, QAbstractItemModel
from ..core.common import *
import re


class OrderTreeModel(QAbstractItemModel):
    """"""
    order_reg = re.compile(u'订单[0-9]+')

    def __init__(self, order):
        super(OrderTreeModel, self).__init__()
        self.__root = QStandardItem()
        self.append_orders(order)

    def data(self, index, role=Qt.DisplayRole):
        """获取index位置的数据"""
        if not index.isValid():
            return QVariant()
        if role == Qt.TextColorRole:
            node = self.node_from_index(index)
            string = node.text()
            if OrderTreeModel.order_reg.match(string):  # 订单结点
                profit_child = node.child(6)            # 第6个孩子结点是收益结点
                if '-' in profit_child.text():          # 收益为负，订单结点绿色，否则红色
                    return QBrush(QColor(0, 180, 0))
                else:
                    return QBrush(QColor(255, 0, 0))
        elif role == Qt.DisplayRole:
                node = self.node_from_index(index)
                return QVariant(node.text())
        else:
            return QVariant()

    def node_from_index(self, index):
        if index.isValid():
            return index.internalPointer()
        else:
            return self.__root

    def index(self, row, column, parent=None, *args, **kwargs):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if not parent.isValid():
            parent_item = self.__root
        else:
            parent_item = parent.internalPointer()
        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QModelIndex()

    def parent(self, index=None):
        if not index.isValid():
            return QModelIndex()
        child_item = index.internalPointer()
        parent_item = child_item.parent()
        if parent_item == self.__root:
            return QModelIndex()
        return self.createIndex(parent_item.row(), 0, parent_item)

    def columnCount(self, parent=None, *args, **kwargs):
        return 1

    def rowCount(self, parent=None, *args, **kwargs):
        if not parent.isValid():
            parent_item = self.__root
        else:
            parent_item = parent.internalPointer()
        return parent_item.rowCount()

    def append_orders(self, orders):
        for i, order in enumerate(orders):
            order_item = QStandardItem(self.tr('订单') + str(i))
            self.append_order_details(order_item, order)
            self.__root.appendRow(order_item)

    def append_order_details(self, order_item, order):
        order_id = QStandardItem(self.tr('订单编号： ' + str(order.order_id)))
        strategy_id = QStandardItem(self.tr('策略编号： ') + str(order.strategy_id))
        symbol = QStandardItem(self.tr('品种： ') + str(order.symbol))
        direction = self.tr('买入') if order.type == ORDER_BUY else self.tr('卖出')
        direction = QStandardItem(self.tr('方向： ') + direction)
        price = QStandardItem(self.tr('开仓价： ') + str(order.price))
        open_time = QStandardItem(self.tr('开仓时间： ') + str(order.order_time))
        order_profit = QStandardItem(self.tr('总盈利： ') + str(order.profit))
        close_profit = QStandardItem(self.tr('每次平仓盈利'))
        for item in zip(order.get_close_profit_list(), order.get_close_time_list()):
            cp = QStandardItem(str(item[1]) + self.tr(': ') + str(item[0]))
            close_profit.appendRow(cp)

        order_item.appendRow(order_id)
        order_item.appendRow(strategy_id)
        order_item.appendRow(symbol)
        order_item.appendRow(direction)
        order_item.appendRow(price)
        order_item.appendRow(open_time)
        order_item.appendRow(order_profit)
        order_item.appendRow(close_profit)
