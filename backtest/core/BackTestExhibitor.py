# coding=utf-8
from PyQt4 import QtGui
from PyQt4.QtCore import QTextCodec
import matplotlib
matplotlib.use('Qt4Agg')
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from pylab import mpl
from ..ui.backtest_exhibition_window import Ui_back_test_dialog
from ..ui.OrderTreeExhibitor import OrderTreeModel


class ExhibitionSubWindow(QtGui.QDialog):
    """
    回测结果展示窗口
    """
    def __init__(self, bt, parent=None):
        QTextCodec.setCodecForTr(QTextCodec.codecForName('utf-8'))  # qt中文字体
        mpl.rcParams['font.sans-serif'] = ['SimHei']  # matplotlib中文指定默认字体
        mpl.rcParams['axes.unicode_minus'] = False     # 解决保存图像是负号'-'显示为方块的问题

        super(ExhibitionSubWindow, self).__init__(parent)

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ui = Ui_back_test_dialog()
        self.ui.setupUi(self)
        self.ui.equity_plot_layout.addWidget(self.toolbar)
        self.ui.equity_plot_layout.addWidget(self.canvas)

        self.order_model = None

        self.equity_axis = self.figure.add_subplot(111)

        self._backtest = bt
        self._backtest.set_exhibitor(self)

    def get_equity_axis(self):
        return self.equity_axis

    def get_canvas(self):
        return self.canvas

    def set_equity_labels(self, equity, dt):
        self.ui.max_equity_label.setText(str(equity))
        self.ui.max_equity_time_label.setText(str(dt))

    def set_drawback_labels(self, db, dt):
        self.ui.max_drawback_rate_label.setText(str(db))
        self.ui.max_drawback_time_label.setText(str(dt))

    def set_order_number_label(self, ordn):
        self.ui.send_order_number_label.setText(str(ordn))

    def closeEvent(self, QCloseEvent):
        super(ExhibitionSubWindow, self).closeEvent(QCloseEvent)
        self._backtest.exit_backtest()

    def set_current_time_label(self, t):
        self.ui.current_time_label.setText(str(t))

    def set_total_order_number(self, n):
        self.ui.total_order_number_label.setText(str(n))

    def set_gross_profit(self, pf):
        self.ui.gross_profit_label.setText(str(pf))

    def set_gross_loss(self, ls):
        self.ui.gross_loss_label.setText(str(ls))

    def set_profit_order_number(self, n):
        self.ui.win_order_number_label.setText(str(n))

    def set_loss_order_number(self, n):
        self.ui.loss_order_number_label.setText(str(n))

    def set_profit(self, n):
        self.ui.total_profit_label.setText(str(n))

    def set_order_infos(self, ods):
        self.order_model = OrderTreeModel(ods)
        self.ui.order_stat_tree_view.setModel(self.order_model)
