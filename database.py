import sqlite3
import json
import os
from datetime import datetime

from config import DB_PATH


def init_database():
    """初始化数据库，创建所有表"""
    # 确保数据库目录存在
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 股票基础信息表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_basic (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        industry TEXT DEFAULT '未知',
        market TEXT DEFAULT '未知',
        price REAL DEFAULT 0,
        total_mv REAL DEFAULT 0,
        update_time TEXT NOT NULL
    )
    ''')

    # 股票价格数据表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_price (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts_code TEXT NOT NULL,
        trade_date TEXT NOT NULL,
        open REAL DEFAULT 0,
        high REAL DEFAULT 0,
        low REAL DEFAULT 0,
        close REAL DEFAULT 0,
        vol REAL DEFAULT 0,
        amount REAL DEFAULT 0,
        UNIQUE(ts_code, trade_date)
    )
    ''')

    # 走势模板表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pattern_template (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_name TEXT UNIQUE NOT NULL,
        pattern_type TEXT NOT NULL,
        data TEXT NOT NULL,
        create_time TEXT NOT NULL
    )
    ''')

    # 回测结果表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS backtest_result (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts_code TEXT NOT NULL,
        strategy_type TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        total_return REAL DEFAULT 0,
        max_drawdown REAL DEFAULT 0,
        win_rate REAL DEFAULT 0,
        create_time TEXT NOT NULL
    )
    ''')

    conn.commit()
    conn.close()


# ---------------------- 股票基础数据操作 ----------------------

def insert_stock_basic(stock_list):
    """插入/更新股票基础信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for stock in stock_list:
        cursor.execute('''
        INSERT OR REPLACE INTO stock_basic 
        (ts_code, name, industry, market, price, total_mv, update_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (stock['ts_code'], stock['name'], stock['industry'],
              stock['market'], stock['price'], stock['total_mv'], update_time))
    conn.commit()
    conn.close()


def get_stock_basic(filter_params=None):
    """获取股票基础信息，支持筛选"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT ts_code, name, industry, market, price, total_mv FROM stock_basic WHERE 1=1"
    args = []
    if filter_params:
        if filter_params.get('industry'):
            query += " AND industry = ?"
            args.append(filter_params['industry'])
        if filter_params.get('market'):
            query += " AND market = ?"
            args.append(filter_params['market'])
        if filter_params.get('price_min') is not None:
            query += " AND price >= ?"
            args.append(filter_params['price_min'])
        if filter_params.get('price_max') is not None:
            query += " AND price <= ?"
            args.append(filter_params['price_max'])
        if filter_params.get('total_mv_min') is not None:
            query += " AND total_mv >= ?"
            args.append(filter_params['total_mv_min'])
        if filter_params.get('total_mv_max') is not None:
            query += " AND total_mv <= ?"
            args.append(filter_params['total_mv_max'])
        if filter_params.get('stock_code'):
            query += " AND ts_code LIKE ?"
            args.append(f"%{filter_params['stock_code']}%")
        if filter_params.get('stock_name'):
            query += " AND name LIKE ?"
            args.append(f"%{filter_params['stock_name']}%")
    cursor.execute(query, args)
    cols = [desc[0] for desc in cursor.description]
    result = [dict(zip(cols, row)) for row in cursor.fetchall()]
    conn.close()
    return result


def get_industry_list():
    """获取stock_basic表中所有行业（去重）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT industry FROM stock_basic WHERE industry IS NOT NULL AND industry != ''")
    industries = [row[0] for row in cursor.fetchall()]
    conn.close()
    return industries

# ---------------------- 股票价格数据操作 ----------------------

def insert_stock_price(price_list):
    """插入股票价格数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for price in price_list:
        cursor.execute('''
        INSERT OR REPLACE INTO stock_price 
        (ts_code, trade_date, open, high, low, close, vol, amount)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (price['ts_code'], price['trade_date'], price['open'], price['high'],
              price['low'], price['close'], price['vol'], price['amount']))
    conn.commit()
    conn.close()


def get_stock_price(ts_code, start_date=None, end_date=None):
    """获取单只股票价格数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT trade_date, open, high, low, close, vol, amount FROM stock_price WHERE ts_code = ?"
    args = [ts_code]
    if start_date:
        query += " AND trade_date >= ?"
        args.append(start_date)
    if end_date:
        query += " AND trade_date <= ?"
        args.append(end_date)
    query += " ORDER BY trade_date ASC"
    cursor.execute(query, args)
    cols = [desc[0] for desc in cursor.description]
    result = [dict(zip(cols, row)) for row in cursor.fetchall()]
    conn.close()
    return result


# ---------------------- 模板数据操作 ----------------------

def insert_pattern(template_name, pattern_type, data):
    """插入走势模板"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
    INSERT OR REPLACE INTO pattern_template 
    (template_name, pattern_type, data, create_time)
    VALUES (?, ?, ?, ?)
    ''', (template_name, pattern_type, json.dumps(data), create_time))
    conn.commit()
    conn.close()


def get_all_patterns():
    """获取所有模板"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, template_name AS name, pattern_type AS type FROM pattern_template ORDER BY create_time DESC")
    cols = [desc[0] for desc in cursor.description]
    result = [dict(zip(cols, row)) for row in cursor.fetchall()]
    conn.close()
    return result


def get_pattern_by_id(pattern_id):
    """根据ID获取模板详情"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT template_name, pattern_type, data FROM pattern_template WHERE id = ?", (pattern_id,))
    res = cursor.fetchone()
    conn.close()
    if res:
        return {
            'name': res[0],
            'type': res[1],
            'data': json.loads(res[2])
        }
    return None


# ---------------------- 回测结果操作 ----------------------

def insert_backtest_result(result_data):
    """插入回测结果"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
    INSERT INTO backtest_result 
    (ts_code, strategy_type, start_date, end_date, total_return, max_drawdown, win_rate, create_time)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (result_data['ts_code'], result_data['strategy_type'], result_data['start_date'],
          result_data['end_date'], result_data['total_return'], result_data['max_drawdown'],
          result_data['win_rate'], create_time))
    conn.commit()
    conn.close()