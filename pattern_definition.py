import json
import pandas as pd
from database import insert_pattern
from config import UPLOAD_FOLDER
import os

def parse_draw_pattern(template_name, key_points):
    """解析绘制型模板"""
    pattern_data = {
        'key_points': key_points,
        'type': 'draw'
    }
    insert_pattern(template_name, 'draw', pattern_data)
    return True

def parse_table_pattern(template_name, file_path):
    """解析表格型模板"""
    df = pd.read_excel(file_path)
    required_cols = ['trade_date', 'price']
    if not all(col in df.columns for col in required_cols):
        raise ValueError("表格需包含trade_date和price列")
    table_data = df[required_cols].to_dict('records')
    pattern_data = {
        'table_data': table_data,
        'type': 'table'
    }
    insert_pattern(template_name, 'table', pattern_data)
    # 删除临时文件
    os.remove(file_path)
    return True

def parse_indicator_pattern(template_name, indicator_conditions):
    """解析指标组合型模板"""
    conditions = [cond.strip() for cond in indicator_conditions.split(',') if cond.strip()]
    pattern_data = {
        'indicator_conditions': conditions,
        'type': 'indicator'
    }
    insert_pattern(template_name, 'indicator', pattern_data)
    return True

# 模板查询复用数据库函数
from database import get_all_patterns, get_pattern_by_id