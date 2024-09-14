import akshare as ak    # 导入数据源
import pandas as pd    # 导入pandas库

#作者：量化投资学
#链接：https://xueqiu.com/9584939714/202490471
#hs300_pe_df = ak.stock_a_pe(market="000300.XSHG").iloc[-1708:]    # 获取沪深300的PE和收盘价数据
hs300_pe_df = ak.stock_a_pe("000300.XSHG").iloc[-1708:]    # 获取沪深300的PE和收盘价数据
hs300_pe_pct = hs300_pe_df[['middlePETTM','close']].rank(ascending=True, pct=True)*100    # 计算PE和收盘价的历史百分位
print(hs300_pe_pct)
#hs300_pe_pct.plot(figsize=(16,8),grid=True,title='沪深300估值和价格百分位')    # 画图
hs300_pe_pct.plot(figsize=(16,8),grid=True,title='300percent')
