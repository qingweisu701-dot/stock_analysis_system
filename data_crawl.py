import tushare as ts
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database import insert_stock_basic, insert_stock_price
from config import TUSHARE_TOKEN, DEFAULT_DATA_DAYS
import sqlite3
# 初始化Tushare
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()


def get_last_trade_date():
    """获取最新交易日"""
    today = datetime.now().strftime('%Y%m%d')
    cal = pro.trade_cal(exchange='SSE', start_date='20240101', end_date=today)
    last_trade = cal[cal['is_open'] == 1]['cal_date'].iloc[-1]
    return last_trade


def calculate_tech_index(price_data):
    """
    计算股票技术指标（MA、RSI等）
    :param price_data: 原始价格数据（列表，包含'trade_date','close','open','high','low','vol'等字段）
    :return: 添加了技术指标的价格数据
    """
    if not price_data:
        return []

    # 转换为DataFrame便于计算
    df = pd.DataFrame(price_data)
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df = df.sort_values('trade_date')  # 按日期排序

    # 1. 计算移动平均线（MA5、MA10、MA20）
    df['MA5'] = df['close'].rolling(window=5, min_periods=1).mean()  # 5日均价
    df['MA10'] = df['close'].rolling(window=10, min_periods=1).mean()  # 10日均价
    df['MA20'] = df['close'].rolling(window=20, min_periods=1).mean()  # 20日均价

    # 2. 计算相对强弱指数（RSI14）
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
    rs = gain / loss.replace(0, 0.001)  # 避免除零
    df['RSI14'] = 100 - (100 / (1 + rs))

    # 3. 计算成交量加权平均价（VWAP）
    df['VWAP'] = (df['amount'] / df['vol']).replace(np.inf, 0)  # 成交额/成交量

    # 转换回字典列表（保留原始字段+新增指标）
    result = df.to_dict('records')
    return result


def batch_crawl():
    """批量采集股票基础信息+价格数据（含技术指标）"""
    # 1. 采集基础信息
    basic_df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry,market')

    # 2. 采集最新价格和市值
    last_trade = get_last_trade_date()
    price_df = pro.daily(trade_date=last_trade, fields='ts_code,close,vol,amount')
    mv_df = pro.daily_basic(trade_date=last_trade, fields='ts_code,total_mv')

    # 3. 数据合并
    merge_df = pd.merge(basic_df, price_df, on='ts_code', how='left')
    merge_df = pd.merge(merge_df, mv_df, on='ts_code', how='left')

    # 4. 格式转换
    stock_list = []
    for _, row in merge_df.iterrows():
        stock_list.append({
            'ts_code': row['ts_code'],
            'name': row['name'],
            'industry': row['industry'] if pd.notna(row['industry']) else '未知',
            'market': row['market'] if pd.notna(row['market']) else '未知',
            'price': row['close'] if pd.notna(row['close']) else 0,
            'total_mv': row['total_mv'] / 10000 if pd.notna(row['total_mv']) else 0  # 转为亿元
        })

    # 5. 插入数据库
    insert_stock_basic(stock_list)

    # 6. 采集最近30天价格数据（含技术指标）
    start_date = (datetime.now() - timedelta(days=DEFAULT_DATA_DAYS)).strftime('%Y%m%d')
    for ts_code in basic_df['ts_code'].head(200):  # 限制前100只，避免性能问题
        # 采集原始价格数据
        raw_price_data = crawl_stock_price(ts_code, start_date, last_trade, need_index=False)
        # 计算技术指标
        price_with_index = calculate_tech_index(raw_price_data)
        # 重新插入带指标的数据（覆盖原始数据）
        insert_stock_price(price_with_index)


def crawl_stock_price(ts_code, start_date=None, end_date=None, need_index=True):
    """
    采集单只股票价格数据（可选择是否计算技术指标）
    :param need_index: 是否返回带技术指标的数据
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=DEFAULT_DATA_DAYS)).strftime('%Y%m%d')
    if not end_date:
        end_date = get_last_trade_date()

    # 采集日线数据
    price_df = pro.daily(
        ts_code=ts_code,
        start_date=start_date,
        end_date=end_date,
        fields='ts_code,trade_date,open,high,low,close,vol,amount'
    )

    # 转为列表
    raw_price_data = price_df.to_dict('records')

    # 如需技术指标，调用计算函数
    if need_index:
        return calculate_tech_index(raw_price_data)
    return raw_price_data


def get_real_time_price(ts_code):
    """获取单只股票实时价格数据（含技术指标）"""
    start_date = (datetime.now() - timedelta(days=DEFAULT_DATA_DAYS)).strftime('%Y%m%d')
    end_date = get_last_trade_date()
    return crawl_stock_price(ts_code, start_date, end_date)


def get_stock_basic():
    """获取股票基础信息列表"""
    basic_df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry,market')
    return basic_df.to_dict('records')


def get_stock_list():
    """获取股票列表（供前端下拉框）"""
    return get_stock_basic()


def get_industry_list():
    """获取所有行业列表"""
    try:
        import os
        import sqlite3

        # 使用正确的数据库路径 - db/stock.db
        db_path = os.path.join(os.path.dirname(__file__), 'db', 'stock.db')
        print(f"尝试连接数据库: {db_path}")  # 调试信息

        # 检查数据库文件是否存在
        if not os.path.exists(db_path):
            print(f"数据库文件不存在: {db_path}")
            return []

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 首先检查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='stock_basic'
        """)
        table_exists = cursor.fetchone()

        if not table_exists:
            print("stock_basic 表不存在")
            conn.close()
            return []

        # 查询stock_basic表中的所有行业
        cursor.execute("""
            SELECT DISTINCT industry 
            FROM stock_basic 
            WHERE industry IS NOT NULL AND industry != ''
            ORDER BY industry
        """)

        industries = [row[0] for row in cursor.fetchall()]
        conn.close()

        print(f"从数据库获取的行业列表: {industries}")  # 调试信息
        return industries

    except Exception as e:
        print(f"获取行业列表失败: {e}")
        import traceback
        traceback.print_exc()
        return []