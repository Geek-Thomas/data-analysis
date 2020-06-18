# 在聚宽平台上实现策略

平台：聚宽

开发环境：python3

需要用到的第三方库：talib, sklearn, datetime, numpy, pandas

## 关于策略

本次策略主要是选股策略：包括**均值回归策略**以及基于机器学习中的**随机森林**进行选股的策略

- 均值回归策略

  ratio = (ma - p)/ma

  在每个调仓日进行

  > 计算股票池中所有股票的N日均线
  >
  > 计算股票池中所有股票与均线的偏离度
  >
  > 选取**偏离度最高**的M只股票并调仓

  ```python
  # 获取沪深300成分股
  security = get_index_stocks('000300.XSHG')
  
  sr = pd.Series(index=security)
  
  for stock in sr.index:
  	# 计算每只股票30日均线
      ma = attribute_history(stock, 30)['close'].mean()
      # 获取当前交易日价格
      p = get_price(stock)['open'][-1]
      ratio = (ma - p) / ma # 偏离度越大，则选择该股票
      sr[stock] = ratio
  to_hold = sr.nlargest(n=10).index # 取最大的10支股票
  ```



- 随机森林模型

  模型数据：

  股票来源于使用均值回归策略选出的股票

  选择开始日期和结束日期

  > 注意：有些股票可能上市时间晚于我们选择的开始日期，此时要处理开始日期

  在我们选择的时间区间内，得到当前交易日（start_days）最近30天的股票价格信息，计算相关指标数据(SMA，WMA， MOM)，我们取上一个交易日的数据作为特征加入，然后通过股票是否涨跌获取标签（1-股票相对上一个交易日上涨，0-股票相对上一个交易日下跌）。

  模型构建：

  关于测试集和训练集的选择：我们选择最后一个数据为测试集，其余为训练集。通过对训练集进行训练，获取最后一个数据的预测结果。如果预测值为1，则将该股票加入到持有的股票池中。

  ```python
  def randomforests(stock):
      
      start_date = datetime.date(2015, 1, 9)
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
  
  
      # 获得训练集和测试集,取最后一个数值为测试集，其余为训练集
      x_train = np.array(x_all[:-1])
      x_test = np.array(x_all[-1]).reshape(1, -1)
      y_train = y_all[:-1]
      y_test = y_all[-1]
  
      #开始利用机器学习算法计算，括号里面的n_estimators就是随机森林中包含的树的数目啦
      clf = RandomForestClassifier(n_estimators=40)
      #训练的代码
      clf.fit(x_train, y_train)
      #得到测试结果的代码
      prediction = clf.predict(x_test)
  
      # 返回上涨的股票，加入持仓
      if prediction == 1:
  
          return stock
  ```

## 模拟交易

我们设置每月第一个交易日进行调仓

```python
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
    # stock_list为策略选出的股票
    for stock in context.portfolio.positions:
        if stock not in stock_list:
            order_target_value(stock, 0)
    
    to_buy = [stock for stock in stock_list if stock not in context.portfolio.positions]
    
    if len(to_buy) > 0:
        cash = context.portfolio.available_cash
        cash_every_stock = cash / len(to_buy)
        for stock in to_buy:
            order_value(stock, cash_every_stock)
```



> 完整代码可见**jquant.py**（需在聚宽平台上运行）

最后的回撤结果：

<img src="C:\Users\28499\AppData\Roaming\Typora\typora-user-images\image-20200618110413392.png" alt="image-20200618110413392" style="zoom:50%;" />

​		从结果来看，策略在2017年5月以前表现还是可以的，但是随后长期落后于沪深300指数，最后策略收益竟然是-57.77%。进行分析之后有以下几点原因：1.从策略本身来看，均值回归策略选出的偏离度大的股票，这其中是会包括一些遭遇黑天鹅事件导致很大偏离度的股票的，收益因此不好保证；除此之外，随机森林选择的特征还有进步的空间，使用上述三个指标(SMA-移动平均率，WMA-加权移动平均律, MOM-动量指标)，本身来讲，这三个特征是有一定相关性的，而且对股价的反映程度还不够。因为是参考之前的策略，所以这个策略本身已经落后于市场了；2.从开始下降的时间点来看：2017年[沪深指数](http://summary.jrj.com.cn/hszs/)基本是在国家队操控下运行的，拉升与接盘上证50等所谓的蓝筹绩优股是其主要操控手法。因此我们选出的股票很大概率不在拉升区间，所以导致了第一波的倒退；2018年由于中美贸易战的影响，策略表现进一步恶化。

​		总的来说，策略表现并不乐观。在今后的学习中，我们也将继续对策略进行改进。	

## 感谢

本部分内容分工：

策略选择：张杨芳菲

代码实现：罗涛

