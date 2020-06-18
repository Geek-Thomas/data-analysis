import tushare as ts  # 采取tushare的pro接口
import datetime
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import pickle

# 将数据更新至当天
today = datetime.datetime.now().strftime('%Y%m%d')
# pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pro = ts.pro_api(token='dc27207c34bd852fcc788e6f4cbfbe1b16e5b0f963012d008bf89ea0') # 调取pro

# 获得沪深300指数成分股代码,写入二进制文件
def get_tickers():
    df = pro.index_weight(index_code='399300.SZ', start_date='20200512', end_date=today) # 月度数据,应该隔月获取
    tickers = df['con_code'].values
    # 将股票代码写入二进制文件
    with open('CSI_tickers.pickle', 'wb') as f:
        pickle.dump(tickers, f)
    return tickers
# get_tickers()

# 获取成分股股票数据
def get_data_from_tushare(reload_CSI_300=False):
    benchmarks = ['000300.SH', '000001.SH']
    if reload_CSI_300:
        # 调用函数,获取代码
        tickers = get_tickers()
    else:
        # 文件不存在则写入
        with open('CSI_tickers.pickle', 'rb') as f:
            tickers = pickle.load(f)
    if not os.path.exists('stock_dfs'):
        os.makedirs('stock_dfs')
    
    for benchmark in benchmarks:
        if not os.path.exists(f'stock_dfs/{benchmark[:-3]}'):
            df = pro.index_daily(ts_code='000300.SH', start_date='20000101', end_date=today)
            df.fillna(method='bfill', inplace=True)
            df.reset_index(inplace=True)
            df.set_index('trade_date', inplace=True)
            df.sort_index(inplace=True)
            df.to_csv(r'stock_dfs/{}.csv'.format(benchmark[:-3]))
        else:
            print('{} has existed'.format(benchmark))
   
    # 遍历代码,写入股票数据 
    for ticker in tickers:
        print(ticker)
        if not os.path.exists('stock_dfs/{}.csv'.format(ticker[:-3])):
            # 不存在对应股票数据,则从tushare接口获得数据,写入文件
            df = pro.daily(ts_code=ticker, start_date='20000101', end_date=today)
            df.reset_index(inplace=True)
            df.set_index('trade_date', inplace=True)
            df.sort_index(inplace=True)
            df.to_csv('stock_dfs/{}.csv'.format(ticker[:-3]))
        else:
            print('{} has existed'.format(ticker))





