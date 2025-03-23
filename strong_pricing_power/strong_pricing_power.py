import tushare as ts
import pandas as pd
import datetime
import logging
import time
import os
from tqdm import tqdm

# 设置 Pandas 显示选项
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.set_option('display.float_format', '{:,.2f}'.format)

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def read_tushare_token(file_path='token.txt'):
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except Exception as e:
        logging.error(f"读取 Tushare 令牌失败: {e}")
        return None


def get_date_range(days=365):
    end_date = datetime.datetime.now().strftime('%Y%m%d')
    start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y%m%d')
    return start_date, end_date


def fetch_balance_sheet_data(pro, start_date, end_date):
    logging.info(f"请求资产负债表数据 ({start_date} - {end_date})")
    try:
        df = pro.balancesheet_vip(start_date=start_date, end_date=end_date,
                                  fields='ts_code,end_date,adv_receipts,acct_payable,notes_payable,accounts_receiv,inventories,total_liab,total_assets')
        return df.fillna(0)
    except Exception as e:
        logging.error(f"获取资产负债表数据失败: {e}")
        return pd.DataFrame()


def fetch_company_names(pro, ts_codes):
    try:
        stock_basic = pro.stock_basic(fields='ts_code,name')
        return stock_basic[stock_basic['ts_code'].isin(ts_codes)][['ts_code', 'name']]
    except Exception as e:
        logging.error(f"获取公司名称失败: {e}")
        return pd.DataFrame()


def fetch_roe_and_debt_data(pro, ts_codes, start_date, end_date, csv_file='roe_debt_data.csv'):
    today = datetime.datetime.now().strftime('%Y%m%d')
    file_name = f'roe_data_{today}.csv'
    if os.path.exists(file_name):
        logging.info("使用本地存储的 ROE 数据。")
        return pd.read_csv(file_name)
    logging.info(f"未找到本地 ROE 数据文件，开始请求 ROE 数据，时间范围：{start_date} - {end_date}")
    try:
        roe_df = pd.DataFrame()
        batch_size = 200
        for i in tqdm(range(0, len(ts_codes), batch_size), desc="Fetching ROE & Debt Data"):
            batch_codes = ','.join(ts_codes[i:i + batch_size])
            df = pro.fina_indicator_vip(ts_code=batch_codes, start_date=start_date, end_date=end_date, fields='ts_code,end_date,roe')
            balance_df = pro.balancesheet_vip(ts_code=batch_codes, start_date=start_date, end_date=end_date, fields='ts_code,end_date,total_liab,total_assets')
            balance_df['debt_to_assets'] = balance_df['total_liab'] / balance_df['total_assets']
            merged_df = pd.merge(df, balance_df[['ts_code', 'end_date', 'debt_to_assets']], on=['ts_code', 'end_date'], how='left')
            roe_df = pd.concat([roe_df, merged_df], ignore_index=True)
            time.sleep(1)
        roe_df.to_csv(file_name, index=False)
        logging.info("ROE 数据已保存到本地文件。")
        return roe_df
    except Exception as e:
        logging.error(f"获取 ROE 数据时发生错误: {e}")
        return pd.DataFrame()


def calculate_cash_circulation(df):
    df['cash_circulation'] = df['adv_receipts'] + df['acct_payable'] + df['notes_payable'] - df['accounts_receiv'] - df['inventories']
    return df.sort_values(by='cash_circulation', ascending=False)


def merge_company_info(pro, df, start_date, end_date):
    ts_codes = df['ts_code'].tolist()
    names = fetch_company_names(pro, ts_codes)
    roe_debt_data = fetch_roe_and_debt_data(pro, ts_codes, start_date, end_date)

    # 将 end_date 列转换为字符串类型
    df['end_date'] = df['end_date'].astype(str)
    roe_debt_data['end_date'] = roe_debt_data['end_date'].astype(str)

    df = pd.merge(df, names, on='ts_code', how='left')
    df = pd.merge(df, roe_debt_data, on=['ts_code', 'end_date'], how='left')
    df = df.sort_values(by='end_date', ascending=False).drop_duplicates(subset=['ts_code'], keep='first')
    df['roe'] = df['roe'].map(lambda x: '{:.2f}'.format(x))
    df['debt_to_assets'] = df['debt_to_assets'].map(lambda x: '{:.2f}'.format(x * 100))
    df['cash_circulation_to_assets'] = (df['cash_circulation'] / df['total_assets']).map(lambda x: '{:.2f}'.format(x * 100))
    columns = ['end_date', 'ts_code', 'name', 'roe', 'debt_to_assets', 'cash_circulation_to_assets'] + [col for col in df.columns if col not in ['end_date', 'ts_code', 'name', 'roe', 'debt_to_assets', 'cash_circulation_to_assets']]
    return df[columns]


def save_to_excel(df, filename='result.xlsx'):
    if not df.empty:
        df.to_excel(filename, index=False)
        logging.info(f"数据已保存至 {filename}")


def main():
    token = read_tushare_token()
    if not token:
        return
    pro = ts.pro_api(token)
    start_date, end_date = get_date_range()
    df = fetch_balance_sheet_data(pro, start_date, end_date)
    if df.empty:
        logging.info("未获取到数据")
        return
    df = calculate_cash_circulation(df)
    df = merge_company_info(pro, df, start_date, end_date)
    save_to_excel(df)


if __name__ == "__main__":
    main()
