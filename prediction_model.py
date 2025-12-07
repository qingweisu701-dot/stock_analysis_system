import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from database import get_stock_price


def calculate_rsi(prices, window=14):
    """计算RSI指标"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rs = rs.fillna(0)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def preprocess_data(price_data):
    """数据预处理，构造特征"""
    df = pd.DataFrame(price_data)
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df = df.sort_values('trade_date')

    # 构造技术指标
    df['MA5'] = df['close'].rolling(window=5).mean()
    df['MA10'] = df['close'].rolling(window=10).mean()
    df['RSI'] = calculate_rsi(df['close'])

    # 填充缺失值
    df = df.fillna(0)

    # 特征和标签
    feature_cols = ['open', 'high', 'low', 'close', 'vol', 'MA5', 'MA10', 'RSI']
    X = df[feature_cols].values
    y = df['close'].shift(-1).values[:-1]  # 下一日收盘价
    X = X[:-1]

    return X, y, df['close'].values


def rf_predict(X, y, current_data):
    """随机森林预测"""
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # 预测下一日价格
    next_price = model.predict([current_data])[0]

    # 计算准确率
    y_pred = model.predict(X_test)
    accuracy = 1 - (mean_squared_error(y_test, y_pred) / np.var(y_test))

    return next_price, round(accuracy, 4)


def lstm_predict(X, y, current_data):
    """LSTM预测"""
    # 数据reshape
    X = X.reshape(X.shape[0], 1, X.shape[1])
    current_data = current_data.reshape(1, 1, current_data.shape[0])

    # 构建模型
    model = Sequential()
    model.add(LSTM(50, input_shape=(1, X.shape[2])))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')
    model.fit(X, y, epochs=50, batch_size=32, verbose=0)

    # 预测
    next_price = model.predict(current_data, verbose=0)[0][0]
    y_pred = model.predict(X, verbose=0).flatten()
    accuracy = 1 - (mean_squared_error(y, y_pred) / np.var(y))

    return next_price, round(accuracy, 4)


def predict_buy_sell(ts_code, model_type='rf'):
    """买卖点预测主函数"""
    price_data = get_stock_price(ts_code)
    if len(price_data) < 60:
        raise ValueError("数据不足，无法预测")

    X, y, close_prices = preprocess_data(price_data)
    current_data = X[-1]
    current_price = close_prices[-1]

    # 模型预测
    if model_type == 'lstm':
        next_price, accuracy = lstm_predict(X, y, current_data)
    else:
        next_price, accuracy = rf_predict(X, y, current_data)

    # 判定买卖点
    buy_point = round(current_price * 0.98, 2)
    sell_point = round(current_price * 1.02, 2)

    return {
        'buy_point': buy_point,
        'sell_point': sell_point,
        'next_price': round(next_price, 2),
        'accuracy': accuracy
    }