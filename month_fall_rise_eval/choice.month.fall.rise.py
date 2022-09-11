#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import argparse

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 160)

def parse_args():
    parser = argparse.ArgumentParser(description='fall raise eval')
    parser.add_argument('-t', '--start_year', help = 'start year')

    return parser.parse_args()

def fall_raise_eval(df, start_year = 1991):
	rq = df['交易时间']
	zdf = df['涨跌幅%']
	cnt = 0
	mls = ([], [], [], [], [], [], [], [], [], [], [], [])

	for arq in rq:
		l = arq.split('/')
		y = int(l[0])
		if (y < start_year):
			continue

		m = int(l[1])
		z = float(zdf[cnt])
		mls[m - 1].append(z)
		cnt += 1

	month = 1
	for m in mls:
		sum = 0.0
		for mi in m:
			sum += mi
		print("%2d : %2f"%(month, sum))
		month += 1

	total = 1.0

	ml = [ 2, 4, 8, 11 ]
	ml = [ 1, 10, 11, 12 ]
	#ml = [ 6, 12 ]

	for l in ml:
		mi = mls[l - 1]
		for m in mi:
			total *= (100.0 + m) / 100
			#print(total, m)
	print(total)


if __name__ == "__main__":
	start_year = 1990
	args = parse_args()
	if args.start_year:
		start_year = (int)(args.start_year)
	
	print ("start_year: ", start_year, "\n")

	df = pd.read_csv('choice_data/000001.month.csv')
	fall_raise_eval(df, start_year)
	print("")

	df = pd.read_csv('choice_data/399001.month.csv')
	fall_raise_eval(df, start_year)
	print("")

	df = pd.read_csv('choice_data/399006.month.csv')
	fall_raise_eval(df, start_year)
	print("")
