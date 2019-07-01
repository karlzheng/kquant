#! env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request

import pandas as pd
from pandas.compat import StringIO
from pandas_highcharts.core import serialize

app = Flask(__name__, static_url_path='')

@app.route('/')
def compare(chartID = 'app', chart_type = 'line', chart_height = 500):
    stock_code = "002713.SZ"
    import tushare as ts
    pro = ts.pro_api("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    import datetime
    today = datetime.date.today()
    threeyearsago = today - datetime.timedelta(days=365*3)
    threeyearsagostr = threeyearsago.strftime('%Y%m%d')
    todaystr = today.strftime('%Y%m%d')

    shdf = pro.index_weekly(ts_code='000001.SH', start_date=threeyearsagostr, end_date=todaystr)
    sh = shdf["close"].to_list()
    sh.reverse()
    maxsh = max(sh)

    ssdf = pro.weekly(ts_code=stock_code, start_date=threeyearsagostr, end_date=todaystr)
    ss = ssdf["close"].to_list()
    ss.reverse()
    maxss = max(ss)
    ssnorm = []
    for i in ss:
        ssnorm.append(i * (maxsh) / maxss)
    sh_str = sh.__str__()
    ssnorm_str = ssnorm.__str__()

    stock_code_str = "\'002713.SZ\'"
    return render_template('compare.html', stock_code=stock_code_str, sh=sh_str, ss=ssnorm_str)

if __name__ == "__main__":
    app.run(debug=True)

