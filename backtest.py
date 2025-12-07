import pandas as pd
import numpy as np
from database import get_stock_price, insert_backtest_result


def trend_following_strategy(price_data):
    """趋势跟踪策略（MA5上穿MA10）"""
    df = pd.DataFrame(price_data)
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df = df.sort_values('trade_date')

    df['MA5'] = df['close'].rolling(window=5).mean()
    df['MA10'] = df['close'].rolling(window=10).mean()

    # 信号
    df['signal'] = 0
    df.loc[df['MA5'] > df['MA10'], 'signal'] = 1
    df.loc[df['MA5'] < df['MA10'], 'signal'] = -1

    # 收益计算
    df['daily_return'] = df['close'].pct_change()
    df['strategy_return'] = df['daily_return'] * df['signal'].shift(1)
    df['cumulative_return'] = (1 + df['strategy_return']).cumprod()

    return df


def mean_reversion_strategy(price_data):
    """均值回归策略（MA20）"""
    df = pd.DataFrame(price_data)
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df = df.sort_values('trade_date')

    df['MA20'] = df['close'].rolling(window=20).mean()

    # 信号
    df['signal'] = 0
    df.loc[df['close'] < df['MA20'], 'signal'] = 1
    df.loc[df['close'] > df['MA20'], 'signal'] = -1

    # 收益计算
    df['daily_return'] = df['close'].pct_change()
    df['strategy_return'] = df['daily_return'] * df['signal'].shift(1)
    df['cumulative_return'] = (1 + df['strategy_return']).cumprod()

    return df


def pattern_match_strategy(price_data):
    """形态匹配策略（突破前高前低）"""
    df = pd.DataFrame(price_data)
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df = df.sort_values('trade_date')

    df['high_5'] = df['high'].rolling(window=5).max()
    df['low_5'] = df['low'].rolling(window=5).min()

    # 信号
    df['signal'] = 0
    df.loc[df['close'] > df['high_5'].shift(1), 'signal'] = 1
    df.loc[df['close'] < df['low_5'].shift(1), 'signal'] = -1

    # 收益计算
    df['daily_return'] = df['close'].pct_change()
    df['strategy_return'] = df['daily_return'] * df['signal'].shift(1)
    df['cumulative_return'] = (1 + df['strategy_return']).cumprod()

    return df


def calculate_metrics(df):
    """计算回测指标"""
    # 总收益率
    total_return = (df['cumulative_return'].iloc[-1] - 1) * 100

    # 最大回撤
    df['cum_max'] = df['cumulative_return'].cummax()
    df['drawdown'] = (df['cumulative_return'] - df['cum_max']) / df['cum_max']
    max_drawdown = df['drawdown'].min() * 100

    # 胜率
    win_trades = df[df['strategy_return'] > 0]
    total_trades = df[df['strategy_return'] != 0]
    win_rate = len(win_trades) / len(total_trades) if len(total_trades) > 0 else 0

    return {
        'total_return': round(total_return, 2),
        'max_drawdown': round(max_drawdown, 2),
        'win_rate': round(win_rate, 4)
    }


def backtest_strategy(ts_code, start_date, end_date, strategy_type='trend'):
    """回测主函数"""
    price_data = get_stock_price(ts_code, start_date, end_date)
    if len(price_data) < 30:
        raise ValueError("回测数据不足")

    # 执行策略
    if strategy_type == 'mean_reversion':
        df = mean_reversion_strategy(price_data)
    elif strategy_type == 'pattern_match':
        df = pattern_match_strategy(price_data)
    else:
        df = trend_following_strategy(price_data)

    # 计算指标
    metrics = calculate_metrics(df)

    # 保存结果
    result_data = {
        'ts_code': ts_code,
        'strategy_type': strategy_type,
        'start_date': start_date,
        'end_date': end_date,
        'total_return': metrics['total_return'],
        'max_drawdown': metrics['max_drawdown'],
        'win_rate': metrics['win_rate']
    }
    insert_backtest_result(result_data)

    return metrics