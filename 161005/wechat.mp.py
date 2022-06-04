#-*- coding : utf-8-*-
import numpy as np
import pandas as pd
from pyecharts.charts import Line
from pyecharts import options as opts

data = pd.read_csv('data/161005.net_value.csv')
data['dt_idx'] = pd.to_datetime(data['净值日期'])
data['Close'] = data['复权单位净值']

data.set_index('dt_idx', inplace=True)
data = data.sort_values(by = 'dt_idx', ascending = True)

SHORT_PERIOD = 60
LONG_PERIOD = 60

dc = data['Close']
ma1 = data['Close'].rolling(SHORT_PERIOD).mean()
ma2 = data['Close'].rolling(LONG_PERIOD).mean()

nna = pd.notna
sum = 1.0
buyed = False
len_ma1 = len(ma1)
last_price = 1
now_price = 1
p0 = 0
p1 = 1

while p1 < len_ma1:
	m10 = ma1[p0]
	m11 = ma1[p1]
	m20 = ma2[p0]
	m21 = ma2[p1]
	c = dc[p1]

	if nna(m10) and nna(m11) and nna(m20) and nna(m21):
		if (not buyed):
			#if (c > m10):
			if (c > m10) or (c < last_price * 0.75):
				now_price = c
				sum -= c
				buyed = True
		else:
			if (c < m10) and ( c >	now_price * 1.3):
			#if (c < m10): 
				last_price = c
				sum += c
				last_price = c
				buyed = False
	p0 += 1
	p1 += 1

if (buyed):
	sum += c
	buyed = False

print(sum)
