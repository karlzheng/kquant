#-*- coding : utf-8-*-

import numpy as np
import pandas as pd
from pyecharts.charts import Line
from pyecharts import options as opts

data = pd.read_csv('data/161005.net_value.csv')
s399106 = pd.read_csv('data/szzz399106.csv')

data['dt_idx'] = pd.to_datetime(data['净值日期'])
data['dt'] = pd.to_datetime(data['净值日期'])
data['Close'] = data['复权单位净值'] * 1000

# 证券代码	证券名称	交易时间	开盘价	最高价	最低价	收盘价	涨跌	涨跌幅%	成交量	成交额
s399106['dt'] = pd.to_datetime(s399106['交易时间'])
s399106['dt_idx'] = pd.to_datetime(s399106['交易时间'])
s399106['Close'] = s399106['收盘价'] * 5

data.set_index('dt_idx', inplace=True)
data = data.sort_values(by = 'dt_idx', ascending = True)

s399106.set_index('dt_idx', inplace=True)
s399106 = s399106.sort_values(by = 'dt_idx', ascending = True)

SHORT_PERIOD = 20
LONG_PERIOD = 60

line1 = Line(init_opts = opts.InitOpts(width="1600px", height="850px"))

tooltip_opts = opts.TooltipOpts(is_show = True, trigger_on = "mousemove | click", axis_pointer_type='cross')
datazoom_opts = opts.DataZoomOpts(range_start=0, range_end=100, type_ ="inside");
line1.set_global_opts(tooltip_opts = tooltip_opts, datazoom_opts = datazoom_opts)

line1.add_xaxis(list(data.index))

lopts = opts.LabelOpts(is_show=False, color = 'green');

line1.add_yaxis("fgth_Close", data['Close'], label_opts = lopts)

lopts = opts.LabelOpts(is_show=False, color = 'blue');

line1.add_yaxis("s399106_Close", s399106['Close'], label_opts = lopts)

line1.render("fgth.html")
# line1.render_notebook()
print(s399106['收盘价']['2021-02-10'])
print(s399106['Close']['2021-02-10'])
