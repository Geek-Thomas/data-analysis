import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tushare as ts
import datetime
import dateutil
from context import Context
from GetTick import get_tickers

CASH = 100000
START_DATE = '2012-01-07'
END_DATE = '2020-06-15'

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

trade_cal = get_trade_cal()
# print(trade_cal)

'''
参照聚宽编写股票回测框架
'''

context = Context(CASH, START_DATE, END_DATE)

class G():
    pass

g = G()
 
def set_benchmark():   # 取某个指数作为基准
    context.benchmark = '000300'

# 获取历史数据
def attribute_history(security, count, fields=('open', 'close', 'high', 'vol')):
    '''
    security: 股票代码
    count: 从当日往前回测多少天
    fields: 股票行情数据列
    '''
    end_date = (context.dt - datetime.timedelta(days=1)).strftime('%Y%m%d') # 历史数据，所以从当前交易日回溯一天
    start_date = trade_cal[(trade_cal['is_open'] == 1) & (trade_cal['cal_date'] <= end_date)][-count:].iloc[0, :]['cal_date']
    return attribute_daterange_history(security, start_date, end_date, fields)

def attribute_daterange_history(security, start_date, end_date, fields=('open', 'close', 'high', 'vol')):
    today = context.dt.strftime("%Y%m%d")
    try:
        df = pd.read_csv(f'stock_dfs/{security}.csv', index_col='trade_date', parse_dates=['trade_date'])
    except FileNotFoundError:
        df = ts.get_k_data(security, today, today).iloc[0, :]

    return df.loc[start_date:end_date, :][list(fields)]

# 获取当前交易日（今天）开盘价 
def get_today_data(security):
    today = context.dt.strftime("%Y%m%d")
    try:
        f = open(f'stock_dfs/{security}.csv', 'r')
        data = pd.read_csv(f, index_col='trade_date', parse_dates=['trade_date']).loc[today, :]
    except FileNotFoundError:
        data = ts.get_k_data(security, today, today).iloc[0, :]
    # 停牌
    except KeyError:
        data = pd.Series()
    return data

def set_order_cost(today_data, amount):

    p = today_data['open']
    # 设置一个滑点
    # 卖出时，减0.01
    p -= 0.01
    # 买入时，加0.01
    p += 0.01

    open_tax=0
    close_tax=0.001
    open_commission=0.0003
    close_commission=0.0003
    min_commission=5

    if amount < 0:
        if abs(p * amount) < 10000:
            commission = min_commission
        commission = p * amount * (close_tax + close_commission)
    else:
        if abs(p * amount) < 10000:
            commission = min_commission
        commission = p * amount * (open_tax + open_commission)
    return commission 


# 底层下单函数，更新持仓和资金
def _order(today_data, security, amount):
    '''
    考虑一下四种情况：
    ① 获取不到今日数据：可能是停牌
    ② 资金不够购买目标仓位：调整仓位
    ③ 买入的成交量不是100的整数倍：调整仓位
    ④ 卖出股票时卖出的仓位大于持仓：更新仓位至0
    '''
    
    p = today_data['open']
    # 设置一个滑点
    # 卖出时，减0.01
    p -= 0.01
    # 买入时，加0.01
    p += 0.01

    if len(today_data) == 0:
        print(f'{context.dt}今日停牌') 
        return 
    if context.cash - amount * p < 0:
        amount = int(context.cash / p)
        print(f'{context.dt}现金不足, 已调整为{amount}')
    
    if amount % 100 != 0:
        if amount != -context.positions.get(security, 0):
            amount = int(amount / 100) * 100
            print(f'{context.dt}不是100的倍数，已调整为{amount}')
    
    if context.positions.get(security, 0) < -amount:
        amount = -context.positions.get(security, 0)
        print(f'{context.dt}卖出股票不能超过持仓数，已调整为{amount}')
    

    # 更新持仓
    context.positions[security] = context.positions.get(security, 0) + amount
    # 更新资金账户
    commission = set_order_cost(today_data, amount)
    context.cash -= (amount * p + commission)
    if context.positions[security] == 0:
        del context.positions[security]
    print('当前持仓：{} 当前资金：{:.2f}'.format(context.positions, context.cash))

# 下单
def order(security, amount):
    today_data = get_today_data(security)
    _order(today_data, security, amount)

# 调整持仓至目标持仓
def order_target(security, amount):
    if amount < 0:
        print('数量不能为负，调整为0')
        amount = 0

    today_data = get_today_data(security)
    hold_amount = context.positions.get(security, 0) # TODO:T+1 positions写两个值，closeable amount(今天过后加入) total_amount(今天买的)
    delta_amount = amount - hold_amount
    _order(today_data, security, delta_amount)

# 按照资金下单
def order_value(security, value):
    today_data = get_today_data(security)
    amount = int(value / today_data['open'])
    _order(today_data, security, amount)

# 调整所持仓股票资金至目标仓位
def order_target_value(security, value):
    today_data = get_today_data(security)
    if value < 0:
        print('价值不能为负，已调整为0')
        value = 0
    
    hold_value = context.positions.get(security, 0) * today_data['open']
    delta_value = value - hold_value
    order_value(security, delta_value)

# 回测框架主体
# 绘制两条曲线：持仓收益曲线，基准收益曲线
def run():
    plt_df = pd.DataFrame(index=pd.to_datetime(context.date_range), columns=['value'])
    init_value = context.cash
    initialize(context)
    last_price = {}

    for dt in context.date_range:
        context.dt = dateutil.parser.parse(dt)
        handle_data(context)
        value = context.cash
        for stock in context.positions:
            # 考虑停牌的情况
            today_data = get_today_data(stock)
            if len(today_data) == 0:
                print('今日股票停牌')
                p = last_price[stock]
            else:
                p = get_today_data(stock)['open']
                last_price[stock] = p
            value += p * context.positions[stock]
        plt_df.loc[dt, 'value'] = value
    plt_df['ratio'] = (plt_df['value'] - init_value) / init_value
    
    bm_df = attribute_daterange_history(context.benchmark, context.start_date, context.end_date)
    bm_init = bm_df['open'][0]
    plt_df['benchmark_ratio'] = (bm_df['open'] - bm_init) / bm_init

    plt_df[["ratio", "benchmark_ratio"]].plot()
    plt.show()


# 用户
def initialize(context):
    set_benchmark()
    g.p1 = 5
    g.p2 = 60
    g.security = '000002'
    
    g.days = 0

# 买卖策略
def handle_data(context):
    
    # 双均线策略
    hist = attribute_history(g.security, g.p2)
    ma5 = hist['close'][-g.p1:].mean()
    ma60 = hist['close'].mean()

    if ma5 > ma60 and g.security not in context.positions:
        order_value(g.security, context.cash)
    elif ma5< ma60 and g.security in context.positions:
        order_target(g.security, 0)

    # 设置调仓周期
    # g.days += 1
    # if g.days % 30 == 0:
    #     print('hello')

run()