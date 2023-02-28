#!/usr/bin/env python
# coding: utf-8
import akshare as ak

"""
# sh000001	上证指数
# sz399001	深证成指
# sz399006	创业板指
# sz399300	沪深300
# sz399905  中证500
# sz399311	国证1000
# sz399303	国证2000
"""
def cal_index_percent(symbol="sh000001"):
    idx = ak.stock_zh_index_daily(symbol)

    tail_20 = idx[-21:]
    end_20 = tail_20.iloc[0]
    end_0 = tail_20.iloc[20]
    end_0_close = end_0.close
    end_20_close = end_20.close
    percent = (end_0_close - end_20_close) / end_20_close * 100

    #print("%s %.3f %-*.3f %-*.3f"%(symbol, percent, 10, end_0_close, 10, end_20_close))
    print("{0} {1} {2:>9} {3:>9}".format(symbol, "%.2f"%(percent), end_0_close, end_20_close))
    
    return percent

if __name__ == "__main__":
    symbols = ("sh000001", "sz399001", "sz399006")
    for s in symbols:
        percent = cal_index_percent(s)
