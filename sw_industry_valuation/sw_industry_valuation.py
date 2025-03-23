import pandas as pd
import tushare as ts
import akshare as ak
import logging
from dateutil.relativedelta import relativedelta
from pyecharts import options as opts
from pyecharts.charts import Line, Page
import re

# 计算时间间隔类
class Cal_Last_Date():
    def __init__(self, date, delta_num):
        self.date = date
        self.delta_num = delta_num

    def datedelta_by_year(self):
        end_date = pd.to_datetime(self.date)
        start_date = (end_date + relativedelta(years=-self.delta_num)).strftime("%Y%m%d")
        return start_date

# 计算百分位
def cal_percentile(data_list):
    sorted_list = sorted(data_list)
    return [round(((sorted_list.index(x) + 1) / len(sorted_list)) * 100, 2) for x in data_list]

# 申万行业代码列表
sw_industry_code_list = [
    '801120.SI', '801980.SI', '801200.SI', '801770.SI', '801760.SI', '801750.SI', '801730.SI',
    '801140.SI', '801050.SI', '801010.SI', '801130.SI', '801110.SI', '801030.SI', '801080.SI',
    '801230.SI', '801740.SI', '801790.SI', '801960.SI', '801880.SI', '801710.SI', '801040.SI',
    '801150.SI', '801210.SI', '801890.SI', '801170.SI', '801970.SI', '801160.SI', '801780.SI',
    '801720.SI', '801180.SI', '801950.SI'
]

# 从akshare获取行业pe数据（此处需替换为实际可用接口）
def get_industry_pe_data(code, start_date, end_date):
    try:
        # 这里只是示例，需替换为实际的akshare接口
        pe_data = ak.some_industry_pe_api(ts_code=code, start_date=start_date, end_date=end_date)
        return pe_data
    except Exception as e:
        logging.error(f"获取 {code} 的pe数据时出错: {e}")
        return pd.DataFrame()

# 获取申万行业估值历史数据
def get_sw_industry_valuation_history_data(pro, date, years_length):
    if not re.match(r'\d{8}', date):
        logging.error(f"日期格式错误: {date}，应为 YYYYMMDD 格式。")
        return

    file_name = 'Industry_Thermometer_DataSource.xlsx'
    with pd.ExcelWriter(file_name) as writer:
        columns = ['交易日期', '行业名称', '收盘价', 'PE', 'PE_温度', 'PB', 'PB_温度', 'ERP', 'ERP_温度', '行业综合温度']

        # 获取国债收益率数据
        bond_zh_us_rate_df = ak.bond_zh_us_rate()
        if bond_zh_us_rate_df.empty:
            logging.error("未能获取国债收益率数据。")
            return

        df_bond_10 = bond_zh_us_rate_df[['日期', '中国国债收益率10年']].rename(columns={'日期': 'trade_date', '中国国债收益率10年': 'Bond10Year'})
        df_bond_10['trade_date'] = df_bond_10['trade_date'].astype(str).str.replace('-', '')

        # 计算时间范围
        cal_date = Cal_Last_Date(date, years_length)
        last_years_length_date = cal_date.datedelta_by_year()

        valid_sheets = 0
        for code in sw_industry_code_list:
            df_2014 = pro.index_daily(ts_code=code, start_date=last_years_length_date, end_date='20211231')
            df_2021 = pro.index_daily(ts_code=code, start_date='20220104', end_date=date)

            # 处理空的或全是 NA 的数据帧
            if df_2014.empty:
                df_sw_industry = df_2021.copy()
            elif df_2021.empty:
                df_sw_industry = df_2014.copy()
            else:
                df_sw_industry = pd.concat([df_2021, df_2014], ignore_index=True).bfill()

            # 获取pe数据
            pe_data = get_industry_pe_data(code, last_years_length_date, date)
            if not pe_data.empty:
                df_sw_industry = df_sw_industry.merge(pe_data, on='trade_date', how='left')

            if 'pe' not in df_sw_industry.columns:
                print(f"Warning: 'pe' column not found for industry {code}. Skipping calculations.")
                continue

            df_sw_industry['pe_percentile'] = df_sw_industry['pe'].rank(pct=True) * 100
            df_sw_industry['pb_percentile'] = df_sw_industry['pb'].rank(pct=True) * 100

            # 计算 ERP
            df_sw_industry = df_sw_industry.merge(df_bond_10, how='left', on='trade_date')
            df_sw_industry['ERP'] = round((100 / df_sw_industry['pe']) - df_sw_industry['Bond10Year'], 2)
            df_sw_industry['ERP_percentile'] = df_sw_industry['ERP'].rank(pct=True) * 100

            # 计算行业综合温度
            df_sw_industry['Thermometer'] = round(
                df_sw_industry['pe_percentile'] * 0.3 +
                df_sw_industry['pb_percentile'] * 0.3 +
                df_sw_industry['ERP_percentile'] * 0.4, 2
            )

            df_result = df_sw_industry[['trade_date', 'name', 'close', 'pe', 'pe_percentile', 'pb', 'pb_percentile', 'ERP', 'ERP_percentile', 'Thermometer']]
            df_result.columns = columns

            if not df_result.empty:
                industry_name = df_result['行业名称'].iloc[0]
                df_result = df_result.iloc[::-1]
                df_result['交易日期'] = pd.to_datetime(df_result['交易日期'], format='%Y%m%d').dt.date
                df_result.to_excel(writer, sheet_name=industry_name, index=False)
                valid_sheets += 1
            else:
                print(f"Warning: No data available for industry {industry_name}. Skipping sheet creation.")

        if valid_sheets == 0:
            pd.DataFrame({"Warning": ["No valid industry data available"]}).to_excel(writer, sheet_name="Empty")

# 可视化行业估值
def visualize_data():
    file_name = "Industry_Thermometer_DataSource.xlsx"
    try:
        excel_total = pd.ExcelFile(file_name)
    except FileNotFoundError:
        logging.error(f"未找到文件: {file_name}")
        return

    sheet_names = excel_total.sheet_names
    page = Page()

    industry_code_str = "<br>".join(sw_industry_code_list)
    page.add(
        Line()
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="申万行业估值分析",
                subtitle=f"行业代码列表:\n{industry_code_str}",
                pos_left="center",
                title_textstyle_opts=opts.TextStyleOpts(font_size=18)
            )
        )
    )

    for industry_name, industry_code in zip(sheet_names, sw_industry_code_list):
        if industry_name == "Empty":
            continue
        df_data = excel_total.parse(industry_name)
        # 检查列名是否存在
        if '交易日期' not in df_data.columns:
            logging.error(f"在 {industry_name} 工作表中未找到 '交易日期' 列")
            continue

        date_list = df_data['交易日期'].tolist()

        line_chart = (
            Line(init_opts=opts.InitOpts(bg_color='white', width='1920px', height='750px'))
            .add_xaxis(date_list)
            .add_yaxis('收盘价', df_data['收盘价'].tolist(), color='red', yaxis_index=0, linestyle_opts=opts.LineStyleOpts(width=4))
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title=f"{industry_name} ({industry_code})",
                    pos_left="center",
                    title_textstyle_opts=opts.TextStyleOpts(font_size=16)
                ),
                toolbox_opts=opts.ToolboxOpts(is_show=True)
            )
        )

        pe_chart = (
            Line()
            .add_xaxis(date_list)
            .add_yaxis('PE', df_data['PE'].tolist(), color='blue', yaxis_index=1, linestyle_opts=opts.LineStyleOpts(width=3))
        )

        pe_percentile_chart = (
            Line()
            .add_xaxis(date_list)
            .add_yaxis('PE_温度', df_data['PE_温度'].tolist(), color='orange', yaxis_index=1, linestyle_opts=opts.LineStyleOpts(width=3))
        )

        line_chart.overlap(pe_chart)
        line_chart.overlap(pe_percentile_chart)
        page.add(line_chart)

    page.render('result.html')

# 读取 Tushare token
def read_tushare_token(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except Exception as e:
        logging.error(f"读取文件时发生错误: {e}")
        return None

# 主程序入口
if __name__ == "__main__":
    token_file = 'token.txt'
    token = read_tushare_token(token_file)
    if not token:
        logging.error("未能获取 Tushare 令牌")
        exit(1)

    ts.set_token(token)
    pro = ts.pro_api()

    date = '20300101'
    years_length = 30

    get_sw_industry_valuation_history_data(pro, date, years_length)
    visualize_data()
    
