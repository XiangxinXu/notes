# coding=utf-8

# ######################### 数学相关常量 ############################# #
FLOAT_PRECISION_TOLERANCE = 1e-6

# ######################### 错误字符串常量 ########################### #
COMMON_ERROR_POSITION = 'file: {0}, function: {1}, line: {2}.'
DATAGENERATOR_START_END_TYPE_ERROR = 'start 和 end 类型应该为str。'
DATAGENERATOR_START_END_VALUE_ERROR = 'start 应早于 end：{0} 行。'
DATAGENERATOR_SYMBOL_TYPE_ERROR = 'sym 应该为set类型。'
BACK_TEST_ENGINE_TYPE_ERROR = '数据传输类型错误。'
TIME_PERIOD_VALUE_ERROR = '周期设置非法。'
BUFFER_NAME_ILLEGAL = '数组名非法。'
BUFFER_ALLOCATION_FAILURE = '数组设置失败。'
BUFFER_NOT_ALLOCATED = '数组未分配。'
BUFFER_INDEX_ERROR = '数组下标设置错误。'
MODE_TYPE_ERROR = '回测模式设置错误。'
ACCOUNT_LOSE = '爆仓了！'

# ######################### 时间类常量 ############################### #
TIME_STEP_1MINUTE = 1001
TIME_STEP_5MINUTE = 1002
TIME_STEP_15MINUTE = 1003
TIME_STEP_1HOUR = 1004
TIME_STEP_4HOUR = 1005
TIME_STEP_1DAY = 1006
TIME_STEP_1WEEK = 1007

# ######################## MongoDB相关常量 ############################ #
MONGO_HOST_IP = '192.168.0.158'    # 服务器地址
MONGO_HOST_PORT = 27017              # 服务器端口号
MONGO_FOREX = 'forex'               # 外汇数据库
# 外汇数据库集合字段名_______________________________________
FOREX_SERVERTIME_T = 'servertime'
FOREX_LOCALTIME_T = 'localtime'
FOREX_BID_T = 'bid'
FOREX_ASK_T = 'ask'
FOREX_SYMBOL = 'symbol'
MONGO_ID = '_id'
FOREX_DATETIME_B = 'date_time'
FOREX_VOLUME_B = 'volume'
FOREX_OPEN_B = 'open'
FOREX_CLOSE_B = 'close'
FOREX_HIGH_B = 'high'
FOREX_LOW_B = 'low'
# ------------------------------------------------------------
# 外汇数据库集合名称__________________________________________
FOREX_XAUUSD = 'XAUUSD'
FOREX_USDJPY = 'USDJPY'
FOREX_XAGUSD = 'XAGUSD'
# ------------------------------------------------------------
# 外汇数据库集合时间粒度，后缀名------------------------------
BAR_1M = '_1MBAR'
BAR_5M = '_5MBAR'
BAR_15M = '_15MBAR'
BAR_1H = '_1HBAR'
BAR_4H = '_4HBAR'
BAR_1D = '_1DBAR'
BAR_1W = '_1WBAR'
# ------------------------------------------------------------
FOREX_TIME_FOMAT = '%Y.%m.%d %H:%M:%S'  # 外汇数据库时间格式


# ######################### 交易市场相关 ############################### #
MARKET_TYPE_FOREX = 2001
MARKET_TYPE_STOCK = 2002
MARKET_TYPE_FUTURE = 2003
MARKET_TYPE_OPTION = 2004

# ######################### 回测模式 #################################### #
BACK_TEST_MODE_ONBAR = 101
BACK_TEST_MODE_ONTICK = 102


# ########################## 订单仓位相关 ################################### #
ORDER_BUY = 3001         # 买
ORDER_SELL = 3002        # 卖
ORDER_STATE_PENDING = 3201  # 挂单尚未成交
ORDER_STATE_IN_POSITION = 3202   # 订单未平掉
ORDER_STATE_CANCELLED = 3203  # 订单已取消
ORDER_STATE_CLOSED = 3204  # 订单已关闭
CROSS_ORDER_SUCCEED = 3301  # 订单交易成功
CROSS_ORDER_FAILED = 3302  # 订单交易失败

# ########################## 数组相关 ######################################## #
REVERSED_INDEXING = 4001  # 倒序索引
NORMAL_INDEXING = 4002    # 顺序索引
BUFFER_OPEN = 'O'         # buffer类型名称
BUFFER_CLOSE = 'C'
BUFFER_HIGH = 'H'
BUFFER_LOW = 'L'
BUFFER_VOLUME = 'V'
BUFFER_TIME = 'T'

# ########################### 数据记录相关 ################################### #
EVENT_QUEUE_SIZE = 100000                  # EventProcessor的Queue的默认大小
DATARECORD_EQUITY = 'data_equity'
DATARECORD_ORDERNUM = 'data_order_number'
DATARECORD_TIME = 'data_time'
SAY_HELLO = 'say_hello'                   # 一个使用示例
UI_ENABLED = True
UI_DISABLED = False
