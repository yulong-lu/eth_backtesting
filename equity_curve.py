#======计算资金曲线，想要知道如果投入100美金，最后能获得多少钱

import pandas as pd
import matplotlib.pyplot as plt
pd.set_option('expand_frame_repr', False)
pd.set_option('display.max_rows',1000)

df = pd.read_csv('data_with_signal.csv')


#===为了计算资金曲线，我们先要算出涨跌幅
df['Change'] = (df['Close']/df['Close'].shift()-1)#根据收盘价计算涨跌幅


#===找出开仓和平仓都是哪些行
condition1 = df['Pos'] !=0
condition2 = df['Pos'] != df['Pos'].shift()
open_pos_conditon = condition1 & condition2

condition3 = df['Pos'] !=0
condition4 = df['Pos'] !=df['Pos'].shift(-1)
close_pos_condition = condition3 & condition4

#===对每次交易进行分组，向上填充，找到开仓时的时间
df.loc[open_pos_conditon, 'Start_Time'] = df['Timestamp']
df['Start_Time'].fillna(method='ffill', inplace = True)
df.loc[df['Pos'] == 0, 'Start_Time'] = pd.NaT

#===交易参数
leverage_rate = 1#合约杠杆，假设是1
init_cash = 100#初始资金
c_rate = 0#交易手续费，假设没有手续费
min_margin_rate = 0.15#最低保证金比率
min_margin = init_cash * leverage_rate * min_margin_rate#最低保证金，如果资金剩余达到最低保证金会被强平


#===计算资金曲线

temp = df[df['Pos'] != 0]['Pos']
common_indices = df['Change'].index.isin(temp.index)
#筛选出 df['Change'] 中相应的元素
temp2 = df['Change'][common_indices]

Equity = pd.Series([leverage_rate * init_cash], index=[temp.index[0]])
#递归计算 Equity 的每个元素
print(Equity)
for i in range(1, len(temp)):
    equity_value = Equity.iloc[i - 1] * temp.iloc[i] * temp2.iloc[i] + Equity.iloc[i - 1]
    Equity[temp.index[i]] = equity_value
    # print(equity_value)
#将 equity 列添加到原始 DataFrame
df['Equity'] = Equity

#处理一下开头的NaN值
df['Equity'].fillna(method='ffill', inplace=True)
df['Equity'].fillna(value=init_cash, inplace=True)


#删除不必要的数据
df.drop(['Change', 'Start_Time'],axis=1, inplace =True)


#===将数据存入“btc_equity_equity_curve.csv”文件中,去掉index
df.to_csv('btc_equity_curve.csv', index = False)


# ===画图
plt.plot(df['Timestamp'], df['Equity'])
plt.xlabel('Timestamp')
plt.ylabel('Equity')
plt.title('Equity vs. Timestamp')


# 显示图形
plt.show()
