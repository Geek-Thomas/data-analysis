# 导入函数库
import talib
from jqdata import *
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import datetime
import numpy as np
import pandas as pd

def initialize(context):
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 设置佣金及印花税
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')
    # 设置基准收益-取沪深300指数
    set_benchmark('000300.XSHG')
    
    
    # 获取沪深300成分股
    g.security = get_index_stocks('000300.XSHG')
    
    # 设置均值回归的均值日期- 30days
    g.ma_days = 30
    #持仓的股票数- 10
    g.stock_num = 10
    
    # 设置换仓频率,每个月第一个交易日换仓
    run_monthly(handle, 1)
    
    
def handle(context):
    
    sr = pd.Series(index=g.security)
    
    # 计算每支股票的偏离率
    for stock in sr.index:
        # 计算30日均线
        ma = attribute_history(stock, g.ma_days)['close'].mean()
        # 计算当前交易日的股票价格
        p = get_current_data()[stock].day_open
        
        ratio = (ma - p) / ma
        
        sr[stock] = ratio
    
    # 选出其中偏离最大的十只股票，即为要持仓的股票
    to_hold = sr.nlargest(g.stock_num).index
    
    stock_list=[]
    for stock in to_hold:
        # 再使用随机森林算法，选出十只股票中上涨概率最大的
        
        start_date = datetime.date(2010, 1, 4)
        end_date = datetime.date(2020, 6, 16)
        
        trading_days = list(get_all_trade_days())
        start_days = get_security_info(stock).start_date
        if start_days > start_date:
            start_date = trading_days[trading_days.index(start_days) + 60]
        start_date_index = trading_days.index(start_date)
        end_date_index = trading_days.index(end_date)
    #     print(start_date)
        x_all = []
        y_all = []
        
        
        for index in range(start_date_index, end_date_index):
    
            start_day = trading_days[index-30]
            end_day = trading_days[index]
        #     print(start_day, end_day)
            # 得到计算指标的所有数据
            stock_data = get_price(stock, start_date=start_day, end_date=end_day, frequency='daily', fields=['close'])
            close_prices = stock_data['close'].values
    #         print(close_prices)
    
            #通过数据计算指标
            # -2是保证获取的数据是昨天的，-1就是通过今天的数据计算出来的指标
            sma_data = round(talib.SMA(close_prices)[-2], 3)
            wma_data = round(talib.WMA(close_prices)[-2], 3)
            mom_data = round(talib.MOM(close_prices)[-2], 3)
        #     print(sma_data)
            features = []
            features.append(sma_data)
            features.append(wma_data)
            features.append(mom_data)
    
            label = False
            if close_prices[-1] > close_prices[-2]:
                label = True
            x_all.append(features)
            y_all.append(label)
            X = np.array(x_all)
            y = np.array(y_all)
        #     print(y.shape)
    
    
        # 获得训练集和测试集,取30%为测试集
        split_num = int(0.3 * len(x_all))
        x_train = x_all[:-split_num]
        x_test = x_all[-split_num:]
        y_train = y_all[:-split_num]
        y_test = y_all[-split_num:]
    
        #开始利用机器学习算法计算，括号里面的n_estimators就是森林中包含的树的数目啦
        clf = RandomForestClassifier(n_estimators=40)
        #训练的代码
        clf.fit(x_train, y_train)
        #得到测试结果的代码
        prediction = clf.predict(x_test)
    
        # 看看预测对了没
        accuracy = sum([prediction == y_test])/len(prediction)
    
        stock_list.append((stock, accuracy))
        # print(stock, accuracy)
    
    # 持仓的股票
    to_hold_list = [stock_acc[0] for stock_acc in stock_list if stock_acc[1] > 0.5]
    print(to_hold_list)
    
    
    for stock in context.portfolio.positions:
        if stock not in to_hold_list:
            order_target_value(stock, 0)
    
    to_buy = [stock for stock in to_hold_list if stock not in context.portfolio.positions]
    
    if len(to_buy) > 0:
        cash = context.portfolio.available_cash
        cash_every_stock = cash / len(to_buy)
        for stock in to_buy:
            order_value(stock, cash_every_stock)
    
    