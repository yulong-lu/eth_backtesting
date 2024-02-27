#======该文件是用来生成交易信号的，我们将在下一节使用这个文件生成的交易信号进行回测
import pandas as pd

pd.set_option('expand_frame_repr', False)
pd.set_option('display.max_rows', 1000)

#导入以太币数据
df = pd.read_csv('ETH_1min.csv')
df.drop(['Date','Symbol'],axis=1, inplace= True)

#===数据预处理
# 将Unix Timestamp列改名为Timestamp，并且转换为datetime格式
df.rename(columns = {'Unix Timestamp' : 'Timestamp'}, inplace=True)
df['Timestamp']=pd.to_datetime(df['Timestamp'], unit='ms')
df.set_index('Timestamp',inplace=True)
df.sort_index(inplace=True)

# filename = 'ETH_1min.csv'
# num_lines = sum(1 for l in open(filename))
# skip_rows = num_lines - 100  # 计算需要跳过的行数
# df = pd.read_csv(filename, skiprows=range(1, skip_rows))
# df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
# df.set_index('Timestamp', inplace=True)

#转换成15分钟数据
rule_type = '15T'
df = df.resample(rule=rule_type,label='left', closed='left').agg(
    {
        'Open':'first',
        'High':'max',
        'Low':'min',
        'Close':'last',
        'Volume':'sum'
    }
)

#我们截取17年到最近的数据
start_date = '2019-01-01'
df = df[df.index >= start_date]
df.reset_index(inplace=True)
#去除volume为0的交易周期
# df.dropna(subset=['Open'], inplace=True)#去除一天都没有交易的周期
df=df[df['Volume']>0]#去除成交量为0的交易周期


#===下是布林线策略
#布林线策略大致如下：共有三条线。
#中轨:n根收盘价的移动平均线
#上轨轨:n根收盘价的移动平均线 + m*n根收盘价的标准查差。
#中轨:n根收盘价的移动平均线 - m*n根收盘价的标准差。
# 当前蜡烛的收盘价向上穿过上轨做多，再次向下穿过中轨时候平仓。
#当前蜡烛的收盘价向下穿过下轨做空，再次向上穿过中轨的时候平仓。
#
# 计算交易信号
#不妨使用n=100天的布林线策略，标准差前面的参数m设置为2，来看一下结果
n = 100
m = 2
# 计算均线
df['Median'] = df['Close'].rolling(n, min_periods=1).mean()
# 计算上下轨道
df['Std'] = df['Close'].rolling(n, min_periods=1).std(ddof=0) #ddof代表自由度，默认1，设为0是为了和我们的tradingView一致
df['Upper'] = df['Median'] + m * df['Std']
df['Lower'] = df['Median'] - m * df['Std']

# 找出做多信号
condition1 = df['Close'] > df['Upper'] #当前k线的收盘价>上轨
condition2 = df['Close'].shift(1)<=df['Upper'].shift(1) #之前k线的收盘价 <=上轨
df.loc[condition1 & condition2,'Signal_Long'] = 1 #将产生做多信号的那根k线的signal设置为1

#找出做多平仓信号
condition1 = df['Close']<df['Median']
condition2 = df['Close'].shift(1)>=df['Median'].shift(1)
df.loc[condition1 & condition2, 'Signal_Long'] = 0

# 找出做空信号
condition1 = df['Close'] < df['Lower'] #当前k线的收盘价>上轨
condition2 = df['Close'].shift(1)>=df['Lower'].shift(1) #之前k线的收盘价 <=上轨
df.loc[condition1 & condition2,'Signal_Short'] = -1 #将产生做多信号的那根k线的signal设置为1

#找出做空平仓信号
condition1 = df['Close'] > df['Median']
condition2 = df['Close'].shift(1) <= df['Median'].shift(1)
df.loc[condition1 & condition2, 'Signal_Short'] = 0

#看一下根据做多信号和做空信号这两栏，一共可能出现多少种情况。
# df.drop_duplicates(subset=['Signal_Long', 'Signal_Short'], inplace=True)
# print(df[['Signal_Long','Signal_Short']])
# exit()
#结果如下 Signal_Long  Signal_Short
# 0             NaN           NaN
# 1             NaN           0.0
# 3             0.0           NaN
# 38            1.0           NaN
# 430           NaN          -1.0
# 994           0.0          -1.0
# 6578          1.0           0.0

#合并做多做空信号，去除重复信号
df['Signal'] = df[['Signal_Long','Signal_Short']].sum(axis=1)
temp = df[df['Signal'].notnull()][['Signal']]#去掉空值
temp = temp[temp['Signal']!= temp['Signal'].shift(1)]#去除假信号，比如已经做多了，做多信号又出现
df['Signal'] = temp['Signal']
#删除不必要的列
df.drop(['Median','Std', 'Upper', 'Lower', 'Signal_Long', 'Signal_Short'], axis=1,inplace=True )

# 由signal产生的计算出每天持有仓位
df['Pos'] = df['Signal'].shift()#产生交易信号的第二个线才会买入卖出
df['Pos'].fillna(method='ffill', inplace=True)#向上补全
df['Pos'].fillna(value=0, inplace=True)#刚开始补全为0
#数据保存

df.to_csv('data_with_signal.csv', index=False)



