#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import akshare as ak
from pyecharts.charts import Bar, Page
from pyecharts import options as opts
import os

# 获取上证指数数据
sh_index = ak.stock_zh_index_daily(symbol="sh000001")
sh_index['date'] = pd.to_datetime(sh_index['date'])
sh_index['month'] = sh_index['date'].dt.month
sh_index['year'] = sh_index['date'].dt.year

start_year = 2000
sh_index = sh_index[sh_index['year'] >= start_year]

# 计算每月的汇总数据
monthly_summary = (
    sh_index.groupby(['year', 'month'])
   .agg(
        开盘点数=('open', 'first'),
        收盘点数=('close', 'last')
    )
   .reset_index()
)
monthly_summary['上月收盘点数'] = monthly_summary['收盘点数'].shift(1)
monthly_summary['涨跌百分比'] = (
    (monthly_summary['收盘点数'] - monthly_summary['上月收盘点数']) / monthly_summary['上月收盘点数'] * 100
).round(2)
monthly_summary = monthly_summary.dropna()

# 统计各月份涨跌次数和累计涨跌百分比
cumulative_returns = monthly_summary.groupby('month')['涨跌百分比'].sum().round(2)
monthly_summary['涨跌'] = monthly_summary['涨跌百分比'].apply(lambda x: '涨' if x > 0 else ('跌' if x < 0 else '平'))
monthly_change_counts = monthly_summary.groupby('month')['涨跌'].value_counts().unstack().fillna(0)

# 新增：计算每个月涨跌百分比的乘积（将百分比转化为对应系数进行计算）
def calculate_product(row):
    """
    辅助函数，用于计算每个月里涨跌百分比对应的系数乘积
    """
    percentages = row['涨跌百分比'] / 100 + 1
    product = 1
    for p in percentages:
        product *= p
        #print(product, p)
    return (product - 1)

monthly_product_returns = monthly_summary.groupby('month').apply(calculate_product).round(2)

print("每个月份的涨跌次数统计：")
print(monthly_change_counts)

# 创建各月份涨跌次数柱状图并添加到页面
change_bar = (
    Bar()
   .add_xaxis([f"{i}月" for i in range(1, 13)])
   .add_yaxis("涨次数", monthly_change_counts['涨'].tolist(), color="red")
   .add_yaxis("跌次数", monthly_change_counts['跌'].tolist(), color="green")
   .set_global_opts(
        title_opts=opts.TitleOpts(title=f"各月份涨跌次数（从{start_year}年开始）"),
        xaxis_opts=opts.AxisOpts(name="月份"),
        yaxis_opts=opts.AxisOpts(name="次数"),
        legend_opts=opts.LegendOpts(is_show=True)
    )
)
page = Page(layout=Page.DraggablePageLayout)
page.add(change_bar)

# 创建累加统计的柱状图
cumulative_bar = (
    Bar()
   .add_xaxis([f"{i}月" for i in range(1, 13)])
   .add_yaxis("累计涨跌百分比", cumulative_returns.tolist(), color="orange")
   .set_global_opts(
        title_opts=opts.TitleOpts(title=f"各月份累计涨跌百分比（从{start_year}年开始）"),
        xaxis_opts=opts.AxisOpts(name="月份"),
        yaxis_opts=opts.AxisOpts(name="累计涨跌百分比"),
        legend_opts=opts.LegendOpts(is_show=False)
    )
)
page.add(cumulative_bar)

# 新增：创建各月份涨跌百分比乘积的柱状图
product_bar = (
    Bar()
   .add_xaxis([f"{i}月" for i in range(1, 13)])
   .add_yaxis("涨跌百分比乘积", monthly_product_returns.tolist(), color="purple")
   .set_global_opts(
        title_opts=opts.TitleOpts(title=f"各月份涨跌百分比乘积（从{start_year}年开始）"),
        xaxis_opts=opts.AxisOpts(name="月份"),
        yaxis_opts=opts.AxisOpts(name="涨跌百分比乘积"),
        legend_opts=opts.LegendOpts(is_show=True)
    )
)
page.add(product_bar)

# 为每个月生成柱状图并加入页面
for month in range(1, 13):
    month_data = monthly_summary[monthly_summary['month'] == month]
    years = month_data['year'].astype(str).tolist()
    returns = month_data['涨跌百分比'].tolist()
    bar = (
        Bar()
       .add_xaxis(years)
       .add_yaxis(f"{month}月涨跌幅", returns, color="skyblue")
       .set_global_opts(
            title_opts=opts.TitleOpts(title=f"{month}月涨跌百分比（从{start_year}年开始）"),
            xaxis_opts=opts.AxisOpts(name="年份", axislabel_opts=opts.LabelOpts(rotate=45)),
            yaxis_opts=opts.AxisOpts(name="涨跌百分比"),
            legend_opts=opts.LegendOpts(is_show=False)
        )
    )
    page.add(bar)

# 先渲染生成HTML文件
page.render(f"all_months_returns_with_cumulative_and_change_counts_from_{start_year}.html")

# 获取生成的HTML文件路径
html_file_path = f"all_months_returns_with_cumulative_and_change_counts_from_{start_year}.html"

# 读取HTML文件内容
with open(html_file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# 在文件内容开头插入标题相关的HTML标签（你也可以根据需要调整插入位置）
new_content = f"<h1>A股上证指数12个月份涨跌情况及涨跌幅统计（从 {start_year} 年开始）</h1>{content}"

# 将修改后的内容写回HTML文件
with open(html_file_path, 'w', encoding='utf-8') as file:
    file.write(new_content)

print(f"A股上证指数12个月份涨跌情况及涨跌幅统计（从 {start_year} 年开始），所有图表已生成：all_months_returns_with_cumulative_and_change_counts_from_{start_year}.html")
