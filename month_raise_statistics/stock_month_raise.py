#!/usr/bin/env python
# coding: utf-8

import argparse
import pandas as pd
import tushare as ts
from pyecharts.charts import Bar, Page
from pyecharts import options as opts

def read_tushare_token(file_path='token.txt'):
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except Exception as e:
        logging.error(f"读取 Tushare 令牌失败: {e}")
        return None

token = read_tushare_token()
if not token:
    exit(1)
pro = ts.pro_api(token)


def get_stock_data(start_year, stock_code):
    start_date = f'{start_year}0101'
    # 使用 tushare 获取个股的日行情数据
    stock_data = pro.daily(ts_code=stock_code, start_date=start_date)
    stock_data["date"] = pd.to_datetime(stock_data["trade_date"])
    stock_data["month"] = stock_data["date"].dt.month
    stock_data["year"] = stock_data["date"].dt.year
    stock_data = stock_data[stock_data["year"] >= start_year]
    return stock_data


def calculate_monthly_summary(stock_data):
    monthly_summary = (
        stock_data.groupby(["year", "month"])
       .agg(开盘点数=("open", "first"), 收盘点数=("close", "last"))
       .reset_index()
    )
    monthly_summary["上月收盘点数"] = monthly_summary["收盘点数"].shift(1)
    monthly_summary["涨跌百分比"] = (
        (monthly_summary["收盘点数"] - monthly_summary["上月收盘点数"])
        / monthly_summary["上月收盘点数"]
        * 100
    ).round(2)
    monthly_summary = monthly_summary.dropna()
    return monthly_summary


def calculate_statistics(monthly_summary):
    cumulative_returns = monthly_summary.groupby("month")["涨跌百分比"].sum().round(2)
    monthly_summary["涨跌"] = monthly_summary["涨跌百分比"].apply(
        lambda x: "涨" if x > 0 else ("跌" if x < 0 else "平")
    )
    monthly_change_counts = (
        monthly_summary.groupby("month")["涨跌"].value_counts().unstack().fillna(0)
    )

    def calculate_product(row):
        percentages = row["涨跌百分比"] / 100 + 1
        product = 1
        for p in percentages:
            product *= p
        return product - 1

    monthly_product_returns = (
        monthly_summary.groupby("month").apply(calculate_product).round(2)
    )
    return cumulative_returns, monthly_change_counts, monthly_product_returns


def create_monthly_returns_table(monthly_summary, start_year):
    pivot_table = monthly_summary.pivot(index="year", columns="month", values="涨跌百分比")

    pivot_table = pivot_table.sort_index(ascending=False)

    headers = ["年份"] + [f"{i}月" for i in range(1, 13)]
    rows = []

    for year, row in pivot_table.iterrows():
        new_row = [f'<th style="background-color: #DCDCDC; font-size: 14px; padding: 10px; text-align: center;">{year}</th>']
        for value in row:
            if pd.notna(value):
                if value > 0:
                    bg_color = "#FF9999"
                elif value < -4:
                    bg_color = "#006400"  # 深绿色
                else:
                    bg_color = "#99FF99"
                cell_content = f'<td style="color:black; font-size: 14px; padding: 8px; text-align: center; background-color: {bg_color};">{value}</td>'
            else:
                cell_content = '<td style="font-size: 14px; padding: 8px; text-align: center; background-color: #F9F9F9;"></td>'
            new_row.append(cell_content)
        rows.append(f'<tr style="background-color: #F9F9F9;">' + "".join(new_row) + "</tr>")

    html_content = '<table border="1" style="border-collapse: collapse; width: 80%; margin: 0 auto;">'  # 设置宽度为 80% 并居中

    html_content += "<tr style='background-color: #B0C4DE;'>" + "".join([f"<th style='font-size: 16px; padding: 10px; text-align: center;'>{header}</th>" for header in headers]) + "</tr>"

    html_content += "".join(rows)

    html_content += "</table>"

    return html_content


def create_charts(
    start_year,
    cumulative_returns,
    monthly_change_counts,
    monthly_product_returns,
    monthly_summary,
):
    page = Page(layout=Page.DraggablePageLayout)

    change_bar = (
        Bar()
       .add_xaxis([f"{i}月" for i in range(1, 13)])
       .add_yaxis("涨次数", monthly_change_counts["涨"].tolist(), color="red")
       .add_yaxis("跌次数", monthly_change_counts["跌"].tolist(), color="green")
       .set_global_opts(
            title_opts=opts.TitleOpts(title=f"各月份涨跌次数（从{start_year}年开始）"),
            xaxis_opts=opts.AxisOpts(name="月份"),
            yaxis_opts=opts.AxisOpts(name="次数"),
            legend_opts=opts.LegendOpts(is_show=True),
        )
    )
    page.add(change_bar)

    cumulative_bar = (
        Bar()
       .add_xaxis([f"{i}月" for i in range(1, 13)])
       .add_yaxis("累计涨跌百分比", cumulative_returns.tolist(), color="orange")
       .set_global_opts(
            title_opts=opts.TitleOpts(title=f"各月份累计涨跌百分比（从{start_year}年开始）"),
            xaxis_opts=opts.AxisOpts(name="月份"),
            yaxis_opts=opts.AxisOpts(name="累计涨跌百分比"),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )
    page.add(cumulative_bar)

    product_bar = (
        Bar()
       .add_xaxis([f"{i}月" for i in range(1, 13)])
       .add_yaxis("涨跌百分比乘积", monthly_product_returns.tolist(), color="purple")
       .set_global_opts(
            title_opts=opts.TitleOpts(title=f"各月份涨跌百分比乘积（从{start_year}年开始）"),
            xaxis_opts=opts.AxisOpts(name="月份"),
            yaxis_opts=opts.AxisOpts(name="涨跌百分比乘积"),
            legend_opts=opts.LegendOpts(is_show=True),
        )
    )
    page.add(product_bar)

    for month in range(1, 13):
        month_data = monthly_summary[monthly_summary["month"] == month]
        years = month_data["year"].astype(str).tolist()
        returns = month_data["涨跌百分比"].tolist()
        bar = (
            Bar()
           .add_xaxis(years)
           .add_yaxis(f"{month}月涨跌幅", returns, color="skyblue")
           .set_global_opts(
                title_opts=opts.TitleOpts(title=f"{month}月涨跌百分比（从{start_year}年开始）"),
                xaxis_opts=opts.AxisOpts(
                    name="年份", axislabel_opts=opts.LabelOpts(rotate=45)
                ),
                yaxis_opts=opts.AxisOpts(name="涨跌百分比"),
                legend_opts=opts.LegendOpts(is_show=False),
            )
        )
        page.add(bar)
    return page


def add_title_to_html(html_file_path, start_year, table_content):
    with open(html_file_path, "r", encoding="utf-8") as file:
        content = file.read()

    new_content = f"""
    <h1>个股 {stock_code} 12个月份涨跌情况及涨跌幅统计（从 {start_year} 年开始）</h1>
    {table_content}
    {content}
    """

    with open(html_file_path, "w", encoding="utf-8") as file:
        file.write(new_content)


def main(start_year, stock_code):
    stock_data = get_stock_data(start_year, stock_code)
    monthly_summary = calculate_monthly_summary(stock_data)
    (
        cumulative_returns,
        monthly_change_counts,
        monthly_product_returns,
    ) = calculate_statistics(monthly_summary)
    page = create_charts(
        start_year,
        cumulative_returns,
        monthly_change_counts,
        monthly_product_returns,
        monthly_summary,
    )

    html_file_path = f"monthly_change_rate_{stock_code}_{start_year}.html"
    page.render(html_file_path)

    table_content = create_monthly_returns_table(monthly_summary, start_year)
    add_title_to_html(html_file_path, start_year, table_content)

    print(f"个股 {stock_code} 12个月份涨跌情况及涨跌幅统计（从 {start_year} 年开始），所有图表已生成：{html_file_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="分析个股月度变化率")
    parser.add_argument(
        "-f", "--start_year", type=int, default=2000, help="指定起始年份，默认为2000年"
    )
    parser.add_argument(
        "-s", "--stock_code", type=str, default="600685.SH", help="指定个股代码，默认为600685.SH"
    )
    args = parser.parse_args()

    start_year = args.start_year
    stock_code = args.stock_code
    main(start_year, stock_code)
