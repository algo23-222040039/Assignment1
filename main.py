# -*- coding: utf-8 -*-
"""
Created on Thu May  4 14:47:14 2023

@author: lijia
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from scipy import interpolate
import pandas as pd
from datetime import datetime

'''
1.导入数据
2.训练集是前1000个交易日（保证历史分位数存在）
3.假定只有2种状态：持有或不持有，即全仓或空仓
4.构建方法：首先计算换手率指标的历史分位数；其次计算20日均值与20日标准差；上阈值是mean6+std6；当分位数超过上均值时，卖出
5.3种持仓状态中0只是维持原来的判断，即不改变。
6.按照万分之3.5计算交易费率
7.计算最大回撤、净值曲线等
'''
def excute_strategy(signal,hold,currency,price):
    if signal == -1:
        if hold != 0:
            currency = currency + hold * price *(1-0.00035)
            hold = 0
    elif signal == 1:
        #如果还有现金，全部持有指数。注意费率：currency/(1+3.5%%) = price * hold
        if currency !=0:
            hold = hold + currency/(1+0.00035)/price
            currency = 0
    elif signal == 0:
        hold = hold
        currency = currency
    return hold,currency


def arg_percentile(series, x):
    # 分位数的启始区间
    a, b = 0, 1
    while True:
        # m是a、b的终点
        m = (a+b)/2
        # 可以打印查看求解过程
        # print(np.percentile(series, 100*m), x)
        if np.percentile(series, 100*m) >= x:
            b = m
        elif np.percentile(series, 100*m) < x:
            a = m
        # 如果区间左右端点足够靠近，则退出循环。
        if np.abs(a-b) <= 0.000001:
            break
    return m


def maxdrawdown(return_list):
    """最大回撤率"""
    maxac=np.zeros(len(return_list))
    b=return_list[0]
    for i in range(0,len(return_list)): #遍历数组，当其后一项大于前一项时，赋值给b
        if return_list[i]>b:
            b=return_list[i]
        maxac[i]=b
    print(maxac)
    i=np.argmax((maxac-return_list)/maxac) #结束位置
    if i == 0:
        return 0
    j = np.argmax(return_list[:i])  # 开始位置
    return (return_list[j] - return_list[i]) / (return_list[j])



data = pd.read_csv("data1.csv")
data = np.array(data)

date_all = data[:,0]
exchange_all = data[:,1]
avg_all = data[:,4]




'''
生成历史分位数指标
'''

quantile_all = np.zeros(np.size(date_all))
for i in range(20,np.size(date_all)):
    quantile_all[i] = arg_percentile(exchange_all[:i], exchange_all[i])
MA20 = np.zeros(np.size(quantile_all))
std_20 = np.zeros(np.size(quantile_all))

#生成了MA20历史分位数
for i in range(np.size(quantile_all)):
    if i >= 20:
        MA20[i] = np.average(quantile_all[i-20:i])
        std_20[i] = np.std(quantile_all[i-20:i]) 
'''
去除前40个数据
'''

date_all = date_all[40:]
exchange_all = exchange_all[40:]
avg_all = avg_all[40:]
quantile_all = quantile_all[40:]
MA20 = MA20[40:]
std_20 = std_20[40:]

'''
在1000天后进行回测
'''
date_test = date_all[1000:]
exchange_test = exchange_all[1000:]
avg_test = avg_all[1000:]
quantile_test =quantile_all[1000:]
MA20_test = MA20[1000:]
std_20_test = std_20[1000:]

upper_test = [MA20_test[i] + std_20_test[i] for i in range(0,np.size(date_test))]
lower_test = [MA20_test[i] - std_20_test[i] for i in range(0,np.size(date_test))]

'''
生成指标、日持仓量、日货币资金量、日净值
'''

signal = np.zeros(np.size(date_test))
holding = np.zeros(np.size(date_test))
currency = np.zeros(np.size(date_test))
net_value = np.zeros(np.size(date_test))


#Currency代表货币资金，num_hold代表持有量，总净值=货币资金+持有量*指数价格
currency[0] = 10000000
net_value[0] = 10000000
'''
构建策略：当分位数>upper，signal=-1
'''

for i in range(1,np.size(date_test)):
    
    if quantile_test[i] > upper_test[i]:
        signal[i] = 1      
    elif quantile_test[i] < upper_test[i]:
        signal[i] = -1
    else:
        signal[i] = 0
    holding[i],currency[i] = excute_strategy(signal=signal[i], hold=holding[i-1], currency=currency[i-1], price=avg_test[i])
    net_value[i] = holding[i] * avg_test[i] + currency[i]
    
    

'''
图1：策略净值图
'''

xs = [datetime.strptime(d, '%Y/%m/%d').date() for d in date_test]


rcParams['font.family']='sans-serif'
rcParams['font.sans-serif']=['Arial']
fig = plt.figure(figsize=(20,10),dpi=80)


net_value_1 = [i/10000000 for i in  net_value]

plt.plot(xs,net_value_1)
plt.ylabel("Net Value")
plt.title("Net value of the strategy")
    







