import numpy as np
from fastdtw import fastdtw
from database import get_stock_basic, get_stock_price, get_pattern_by_id


def normalize_data(data):
    """数据标准化"""
    data = np.array(data)
    mean = np.mean(data)
    std = np.std(data)
    if std == 0:
        return np.zeros_like(data)
    return (data - mean) / std


def calculate_similarity(template_prices, stock_prices):
    """计算DTW相似度（0-1）"""
    template_norm = normalize_data(template_prices)
    stock_norm = normalize_data(stock_prices)
    distance, _ = fastdtw(template_norm, stock_norm)
    similarity = 1 / (1 + distance)
    return round(similarity, 4)


def match_pattern(pattern_id, filter_params):
    """相似匹配主函数"""
    # 获取模板
    pattern = get_pattern_by_id(pattern_id)
    if not pattern:
        raise ValueError("模板不存在")

    # 提取模板价格序列
    template_prices = []
    if pattern['type'] == 'draw':
        template_prices = [p['price'] for p in pattern['data']['key_points']]
    elif pattern['type'] == 'table':
        template_prices = [p['price'] for p in pattern['data']['table_data']]
    elif pattern['type'] == 'indicator':
        template_prices = [10, 12, 11, 13, 15, 14, 16]  # 默认序列，可优化
    if len(template_prices) < 3:
        raise ValueError("模板价格序列过短")

    # 获取筛选后的股票
    filtered_stocks = get_stock_basic(filter_params)
    if not filtered_stocks:
        return []

    # 遍历计算相似度
    match_results = []
    start_date = filter_params.get('start_date')
    end_date = filter_params.get('end_date')
    for stock in filtered_stocks:
        price_data = get_stock_price(stock['ts_code'], start_date, end_date)
        if len(price_data) < len(template_prices):
            continue
        # 取最近N个价格（N=模板长度）
        stock_prices = [p['close'] for p in price_data[-len(template_prices):]]
        similarity = calculate_similarity(template_prices, stock_prices)
        if similarity >= 0.5:  # 相似度阈值
            match_results.append({
                'ts_code': stock['ts_code'],
                'name': stock['name'],
                'industry': stock['industry'],
                'price': stock['price'],
                'total_mv': stock['total_mv'],
                'match_score': similarity
            })

    # 按相似度排序
    match_results.sort(key=lambda x: x['match_score'], reverse=True)
    return match_results