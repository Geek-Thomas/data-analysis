# 简单回测框架的搭建

在聚宽量化平台上使用策略进行回测之后，想要自己搭建一个简单的回测框架，来实现相对简单的回测功能。

开发环境：python 3.7.7

需要用到的库：pandas, numpy, matplotlib, tushare, datetime, dateutil, os, pickle

## 主要文件

> backTest.py: 实现回测框架
>
> context.py: 定义相关交易信息
>
> GetTick.py： 更新沪深300成分股股票数据



### GetTick.py

调用tushare的pro接口中的index_weight函数，获取沪深300近一个月的成分股。根据股票代码，调用pro接口中的daily函数，获取相应股票的日线行情，写入csv文件

```python
# 将数据更新至当天
today = datetime.datetime.now().strftime('%Y%m%d')
# pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pro = ts.pro_api(token=***) # 调取pro接口

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
    # 两个成分股，沪深300指数以及上证指数
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
```



### context.py



```python
# 使用tushare接口获取交易日
pro = ts.pro_api(token=***)

# 获取交易日
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
        self.dt = None
```



### backTest.py

在主体的`回测框架中`，我们参照聚宽的回测框架，定义了如下几个函数：

- attribute_history：获取股票历史数据

  ```python
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
  
  
  ```



- get_today_data：获取**当前交易日开盘价**

  导入GetTick获得的交易数据，从中获得当前交易日开盘价

  ```python
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
  ```



- set_order_cost：简单设置交易佣金手续费

  这里根据实际简单设计了滑点，佣金和手续费

  ```python
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
  ```



- 下单函数

  这里涉及到以下几个函数：

  ①_order：底层下单函数，用于更新持仓和资金，考虑了交易过程中可能存在的几个问题：股票停牌、现金不足、买入单不足手以及卖出股票超持仓的情况。

  ②order：根据交易量下单

  ③order_target：根据目标持仓下单

  ④order_value：根据资金下单

  ⑤6order_target_value：调整所持仓股票资金至目标仓位

  ```python
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
  
  ```



- handle_data：实现简单的双均线策略

  ```python
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
  ```

  

- 绘制收益曲线

  ```python
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
  ```

最后的收益曲线：

<img src="C:\Users\28499\AppData\Roaming\Typora\typora-user-images\image-20200618093904157.png" alt="image-20200618093904157" style="zoom:50%;" />



## @总结

实现了简单的双均线策略的回测框架，仍有很多不足。股票仓位的控制，以及如果要实现更复杂的短线策略，需要考虑T+1交易的情况，这是之后需要进一步完善之处。



## 感谢

内容分工：

框架主体：罗涛

数据获取：刘众

下单函数：张杨芳菲