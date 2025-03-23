import tushare as ts
import pandas as pd
import datetime
import logging
import time
import os

# 设置 Pandas 显示选项
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.set_option('display.float_format', '{:,.2f}'.format)

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_tushare_token(file_path):
    try:
        with open(file_path, 'r') as file:
            token = file.read().strip()
            return token
    except FileNotFoundError:
        logging.error(f"未找到文件: {file_path}")
        return None
    except Exception as e:
        logging.error(f"读取文件时发生错误: {e}")
        return None

def get_date_range(days):
    end_date = datetime.datetime.now().strftime('%Y%m%d')
    start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y%m%d')
    return start_date, end_date

def get_balance_sheet_data(pro, start_date, end_date):
    logging.info(f"开始请求资产负债表数据，时间范围：{start_date} - {end_date}")
    try:
        df = pro.balancesheet_vip(start_date=start_date, end_date=end_date,
                                  fields='ts_code,end_date,adv_receipts,acct_payable,notes_payable,accounts_receiv,inventories')
        logging.info("资产负债表数据请求成功")
        return df
    except Exception as e:
        logging.error(f"调用接口时发生错误: {e}")
        return pd.DataFrame()

def get_company_names(pro, ts_codes):
    logging.info("开始请求公司名称数据")
    try:
        stock_basic = pro.stock_basic(fields='ts_code,name')
        names = stock_basic[stock_basic['ts_code'].isin(ts_codes)][['ts_code', 'name']]
        logging.info("公司名称数据请求成功")
        return names
    except Exception as e:
        logging.error(f"获取公司名称时发生错误: {e}")
        return pd.DataFrame()

def filter_companies(df):
    if df.empty:
        logging.info("未获取到符合条件的数据。")
        return pd.DataFrame()
    df = df.fillna(0)
    df['cash_circulation'] = df['adv_receipts'] + df['acct_payable'] + df['notes_payable'] - df['accounts_receiv'] - df['inventories']
    df = df.sort_values(by='cash_circulation', ascending=False)
    logging.info("按现金循环指标排序后的公司:")
    logging.info(df)
    return df

def convert_units(df):
    non_numeric_cols = ['TS股票代码', '报告期', '公司名称', 'ROE']
    for col in df.columns:
        if col not in non_numeric_cols:
            df[col] = df[col].apply(lambda x: f'{x / 1e8:.2f}亿' if x >= 1e8 else f'{x / 1e4:.2f}万')
    return df

def save_result_to_excel(result):
    if not result.empty:
        try:
            column_mapping = {
                "ts_code": "TS股票代码",
                "end_date": "报告期",
                "adv_receipts": "预收款项",
                "acct_payable": "应付账款",
                "notes_payable": "应付票据",
                "accounts_receiv": "应收账款",
                "inventories": "存货",
                "cash_circulation": "现金循环指标",
                "name": "公司名称",
                "roe": "ROE"
            }
            result = result.rename(columns=column_mapping)
            result = convert_units(result)
            result.to_excel('result.xlsx', index=False)
            logging.info("结果已按要求排序并保存到 result.xlsx 文件中。")
        except Exception as e:
            logging.error(f"保存结果到 Excel 文件时发生错误: {e}")
    else:
        logging.info("没有结果可保存到 Excel 文件。")

def get_roe_data(pro, ts_codes, start_date, end_date):
    today = datetime.datetime.now().strftime('%Y%m%d')
    file_name = f'roe_data_{today}.csv'
    if os.path.exists(file_name):
        logging.info("使用本地存储的 ROE 数据。")
        return pd.read_csv(file_name)
    logging.info(f"未找到本地 ROE 数据文件，开始请求 ROE 数据，时间范围：{start_date} - {end_date}")
    try:
        roe_df = pd.DataFrame()
        batch_size = 200
        total_batches = len(ts_codes) // batch_size + (1 if len(ts_codes) % batch_size != 0 else 0)
        for i in range(0, len(ts_codes), batch_size):
            batch_codes = ','.join(ts_codes[i:i + batch_size])
            batch_num = i // batch_size + 1
            logging.info(f"正在请求第 {batch_num} 批 ROE 数据，共 {total_batches} 批")
            df = pro.fina_indicator_vip(ts_code=batch_codes, start_date=start_date, end_date=end_date, fields='ts_code,end_date,roe')
            print(df)
            roe_df = pd.concat([roe_df, df], ignore_index=True)
            time.sleep(1)
        roe_df.to_csv(file_name, index=False)
        logging.info("ROE 数据已保存到本地文件。")
        return roe_df
    except Exception as e:
        logging.error(f"获取 ROE 数据时发生错误: {e}")
        return pd.DataFrame()

def find_companies_with_high_adv_receipts():
    token_file = 'token.txt'
    token = read_tushare_token(token_file)
    if not token:
        logging.error("未能获取到有效的 Tushare 令牌，无法继续操作。")
        return pd.DataFrame()

    pro = ts.pro_api(token)
    start_date, end_date = get_date_range(365)
    df = get_balance_sheet_data(pro, start_date, end_date)
    result = filter_companies(df)

    if not result.empty:
        ts_codes = result['ts_code'].tolist()
        names = get_company_names(pro, ts_codes)
        roe_data = get_roe_data(pro, ts_codes, start_date, end_date)

        # 确保 end_date 列类型一致
        result['end_date'] = result['end_date'].astype(str)
        roe_data['end_date'] = roe_data['end_date'].astype(str)
        
        # 合并公司名称和 ROE 数据
        result = pd.merge(result, names, on='ts_code', how='left')
        result = pd.merge(result, roe_data, on=['ts_code', 'end_date'], how='left')

        # 调整列顺序：公司名称在第二列，ROE 在第三列
        if 'name' in result.columns and 'roe' in result.columns:
            cols = ['ts_code', 'name', 'roe'] + [col for col in result.columns if col not in ['ts_code', 'name', 'roe']]
            result = result[cols]
        else:
            logging.warning("公司名称列或 ROE 列未找到，不进行列顺序调整。")

    return result

if __name__ == "__main__":
    result = find_companies_with_high_adv_receipts()
    save_result_to_excel(result)
