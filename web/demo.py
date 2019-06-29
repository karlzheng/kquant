#! env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request

import pandas as pd
from pandas.compat import StringIO
from pandas_highcharts.core import serialize

app = Flask(__name__, static_url_path='')
#app.secret_key = "2kQOLbr6NtfHV0wIItjHWzuwsgCUXA4CSSBWFE9yELqrkSZU"

@app.route('/')
def graph_Example(chartID = 'app', chart_type = 'line', chart_height = 500):
    data = """Date,Value\n2019-12-31,1.7\n2018-12-31,3.7\n2017-12-31,1.7"""
    df = pd.read_csv(StringIO(data), index_col=0, parse_dates=True)
    df = df.sort_index()
    dataset = serialize(df, render_to='mychart', secondary_y='frags', output_type='json')

    return render_template('graph.html', chart=dataset)

if __name__ == "__main__":
    app.run(debug=True)

