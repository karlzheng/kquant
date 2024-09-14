### 1. 简单移动平均线交叉策略

该策略基于短期和长期移动平均线的交叉点来生成买卖信号。

```python
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

# 下载股票数据
data = yf.download('AAPL', start='2020-01-01', end='2021-01-01')

# 计算短期和长期移动平均线
data['MA_short'] = data['Close'].rolling(window=20).mean()
data['MA_long'] = data['Close'].rolling(window=50).mean()

# 生成交易信号
data['Signal'] = 0
data['Signal'][20:] = np.where(data['MA_short'][20:] > data['MA_long'][20:], 1, 0)
data['Position'] = data['Signal'].diff()
data['Signal'] *= 150


# 可视化结果
plt.figure(figsize=(14,7))
plt.plot(data['Close'], label='收盘价', alpha=0.5)
plt.plot(data['MA_short'], label='短期均线', alpha=0.5)
plt.plot(data['MA_long'], label='长期均线', alpha=0.5)
#plt.plot(data['Position'], label='Pos', alpha=0.5)
plt.plot(data['Signal'], label='Sig', alpha=0.5)

plt.legend()
plt.show()
```

### 2. 动量策略

根据价格的动量（即价格变动的速度和方向）来制定交易决策。

```python
# 计算每日回报率
data['Returns'] = data['Close'].pct_change()

# 计算动量
data['Momentum'] = data['Returns'].rolling(window=10).mean()

# 生成交易信号
data['Signal'] = np.where(data['Momentum'] > 0, 1, -1)
```

### 3. 均值回归策略

假设价格会回归到其平均值，当价格偏离均值一定程度时，进行反向操作。

```python
# 计算价格的 z-score
data['Z-score'] = (data['Close'] - data['Close'].rolling(window=20).mean()) / data['Close'].rolling(window=20).std()

# 生成交易信号
data['Signal'] = np.where(data['Z-score'] > 1, -1, np.where(data['Z-score'] < -1, 1, 0))
```

### 4. 布林带策略

利用布林带的上轨和下轨来识别超买和超卖状态。

```python
# 计算布林带
data['Middle Band'] = data['Close'].rolling(window=20).mean()
data['Upper Band'] = data['Middle Band'] + 1.96 * data['Close'].rolling(window=20).std()
data['Lower Band'] = data['Middle Band'] - 1.96 * data['Close'].rolling(window=20).std()

# 生成交易信号
data['Signal'] = np.where(data['Close'] < data['Lower Band'], 1, np.where(data['Close'] > data['Upper Band'], -1, 0))
```

### 注意事项

- **数据获取**：以上示例使用了 `yfinance` 库来获取历史数据，您可以根据需要选择其他数据源。
- **风险管理**：在实际交易中，应考虑止损、止盈和仓位管理等风险控制措施。
- **回测与优化**：在将策略用于真实交易之前，建议使用历史数据进行回测，并根据结果优化参数。
- **法律合规**：确保您的交易活动符合所在地区的法律法规。

如果您有特定的市场、资产类别或策略思路，请告诉我，我可以提供更有针对性的帮助。