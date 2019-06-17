#! env python
# --coding:utf8--

import tushare as ts
pro = ts.pro_api("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

from sqlalchemy import create_engine
engine = create_engine('mysql://root:xxxxxxxx@127.0.0.1/ts?charset=utf8')
conn = engine.connect()

df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
#df.to_sql("companylist", engine)
cl = df["ts_code"].values.tolist()
for c in cl:
    try:
        df = pro.fina_audit(ts_code=c, start_date='20000101', end_date='20190808')
        df.to_sql("audit", engine, if_exists='append')
    except Exception as e:
        continue

# mysql union query
#use ts;
#select ts_code from companylist where ts_code in (select DISTINCT ts_code from audit where ann_date like "%2019%" and (audit_agency like "%德勤%" or audit_agency like "%普华%" or audit_agency like "%毕马威%"or audit_agency like "%安永%"));

