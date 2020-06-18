import pandas as pd
import datetime
import dateutil
import tushare as ts

# 使用tushare接口获取交易日
pro = ts.pro_api(token='dc27207c34bd852fcc788e6f4cbfbe1b16e5b0f963012d008bf89ea0')
def get_trade_cal(trade=True):
    if trade:
        trade_cal = pro.trade_cal()
        trade_cal.to_csv('trade_cal.csv')
        trade = False
    else:
        trade_cal = pd.read_csv('trade_cal.csv', index_col=0)
        # print(trade)
    return trade_cal
# 上下文信息保存：储存账户信息
class Context():
    def __init__(self, cash, start_date, end_date):
        '''
        cash: 初始资金
        start_date: 回测开始时间
        end_date: 回测结束时间
        '''
        self.cash = cash
        self.start_date = start_date
        self.end_date = end_date
        self.positions = {} # 记录持仓
        self.benchmark = None # 基准，取某个指数
        self.dates = pd.date_range(start=start_date, end=end_date, freq='D')\
        .map(lambda x: datetime.datetime.strftime(x, '%Y%m%d')) # 获取日期队列
        self.date_range = get_trade_cal().query("is_open == 1 & cal_date in @self.dates")['cal_date'].values # 获取期间所有交易日数组
        # self.dt = dateutil.parser.parse(start_date) # 开始模拟的时间 # TODO: start_date后一个交易日
        self.dt = None
        
