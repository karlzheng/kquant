#!/usr/bin/env python
# -*- coding: utf-8 -*-

import akshare as ak
import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 160)

s = ak.stock_zh_a_hist(symbol="600685", period="monthly", start_date="20000101", end_date='20220907', adjust="qfq")

rq = (s['日期'])
zdf = s['涨跌幅']
cnt = 0
mls = ([], [], [], [], [], [], [], [], [], [], [], [])
for arq in rq:
	l = arq.split('-')
	m = int(l[1]) - 1
	z = float(zdf[cnt])
	mls[m].append(z)
	cnt += 1

month = 1
for m in mls:
	sum = 0.0
	for mi in m:
		sum += mi
	print("%2d : %2f"%(month, sum))
	month += 1
