import os
import json
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from waitress import serve
from database import init_database
from data_crawl import batch_crawl, crawl_stock_price, get_real_time_price, get_stock_list, get_industry_list
from pattern_definition import (
    parse_draw_pattern, parse_table_pattern, parse_indicator_pattern,
    get_all_patterns, get_pattern_by_id
)
from dtw_matching import match_pattern
from prediction_model import predict_buy_sell
from backtest import backtest_strategy
from config import UPLOAD_FOLDER
from flask import send_from_directory
# 初始化应用
app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'stock.db')
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 初始化数据库
init_database()

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)
# ---------------------- 页面路由 ----------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data_crawl')
def data_crawl_page():
    return render_template('data_crawl.html')

@app.route('/pattern_def')
def pattern_def_page():
    return render_template('pattern_def.html')

@app.route('/matching')
def matching_page():
    return render_template('matching.html')

@app.route('/prediction')
def prediction_page():
    return render_template('prediction.html')

@app.route('/backtest')
def backtest_page():
    return render_template('backtest.html')

# ---------------------- 功能接口 ----------------------
# 1. 数据采集接口
@app.route('/crawl_data', methods=['POST'])
def crawl_data():
    try:
        batch_crawl()
        return jsonify({'code': 200, 'msg': '批量采集成功'})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'采集失败：{str(e)}'})

@app.route('/get_real_time_price', methods=['GET'])
def get_real_time_price_api():
    try:
        ts_code = request.args.get('ts_code')
        data = get_real_time_price(ts_code)
        return jsonify({'code': 200, 'data': data})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'获取失败：{str(e)}'})

@app.route('/get_stock_list', methods=['GET'])
def get_stock_list_api():
    try:
        data = get_stock_list()
        return jsonify({'code': 200, 'data': data})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'获取失败：{str(e)}'})


@app.route('/get_industry_list', methods=['GET'])
def get_industry_list_api():
    try:
        # 直接从 data_crawl 模块导入函数
        from data_crawl import get_industry_list
        data = get_industry_list()
        print(f"获取到的行业数据: {data}")  # 调试信息

        # 确保返回的是列表且过滤空值
        if data and isinstance(data, list):
            # 去重、过滤空值、排序
            cleaned_data = list(set([
                str(industry).strip() for industry in data
                if industry and str(industry).strip() != ''
            ]))
            cleaned_data.sort()
            return jsonify({'code': 200, 'data': cleaned_data})
        else:
            return jsonify({'code': 200, 'data': []})

    except Exception as e:
        print(f"获取行业列表错误: {e}")
        import traceback
        traceback.print_exc()  # 打印详细错误信息
        return jsonify({'code': 500, 'msg': f'获取失败：{str(e)}'})
# 2. 模板定义接口
@app.route('/create_draw_pattern', methods=['POST'])
def create_draw_pattern():
    try:
        template_name = request.form.get('template_name')
        key_points = json.loads(request.form.get('key_points', '[]'))
        if not template_name:
            return jsonify({'code': 400, 'msg': '模板名称不能为空'})
        if len(key_points) < 2:
            return jsonify({'code': 400, 'msg': '至少添加2个关键点'})
        parse_draw_pattern(template_name, key_points)
        return jsonify({'code': 200, 'msg': '绘制型模板创建成功'})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'创建失败：{str(e)}'})

@app.route('/create_table_pattern', methods=['POST'])
def create_table_pattern():
    try:
        template_name = request.form.get('template_name')
        table_file = request.files.get('table_file')
        if not template_name or not table_file:
            return jsonify({'code': 400, 'msg': '名称和文件不能为空'})
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], table_file.filename)
        table_file.save(file_path)
        parse_table_pattern(template_name, file_path)
        return jsonify({'code': 200, 'msg': '表格型模板创建成功'})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'创建失败：{str(e)}'})

@app.route('/create_indicator_pattern', methods=['POST'])
def create_indicator_pattern():
    try:
        template_name = request.form.get('template_name')
        conditions = request.form.get('indicator_conditions')
        if not template_name or not conditions:
            return jsonify({'code': 400, 'msg': '名称和条件不能为空'})
        parse_indicator_pattern(template_name, conditions)
        return jsonify({'code': 200, 'msg': '指标型模板创建成功'})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'创建失败：{str(e)}'})

@app.route('/get_patterns', methods=['GET'])
def get_patterns_api():
    try:
        data = get_all_patterns()
        return jsonify({'code': 200, 'data': data})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'获取失败：{str(e)}'})

# 3. 相似匹配接口
@app.route('/match_pattern', methods=['POST'])
def match_pattern_api():
    try:
        pattern_id = request.form.get('pattern_id')
        industry = request.form.get('industry') or None

        print(f"匹配请求 - pattern_id: {pattern_id}, industry: {industry}")  # 调试信息

        # 简化过滤参数，只使用前端传递的参数
        filter_params = {
            'industry': industry
            # 其他参数使用默认值或None
        }

        data = match_pattern(pattern_id, filter_params)
        return jsonify({'code': 200, 'data': data})

    except Exception as e:
        print(f"匹配错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'msg': f'匹配失败：{str(e)}'})
# 4. 匹配结果导出
@app.route('/export_match_result', methods=['POST'])
def export_match_result():
    try:
        pattern_id = request.form.get('pattern_id')
        filter_params = {
            'stock_code': request.form.get('stock_code') or None,
            'stock_name': request.form.get('stock_name') or None,
            'industry': request.form.get('industry') or None,
            'market': request.form.get('market') or None,
            'price_min': float(request.form.get('price_min', 0)),
            'price_max': float(request.form.get('price_max', 1000)),
            'total_mv_min': float(request.form.get('total_mv_min', 0)),
            'total_mv_max': float(request.form.get('total_mv_max', 100000)),
            'start_date': request.form.get('start_date') or None,
            'end_date': request.form.get('end_date') or None,
            'north_money_min': float(request.form.get('north_money_min', 0)),
            'longhu_net_min': float(request.form.get('longhu_net_min', 0))
        }
        data = match_pattern(pattern_id, filter_params)
        if not data:
            return jsonify({'code': 400, 'msg': '无数据可导出'})
        df = pd.DataFrame(data)
        file_name = f'match_result_{pattern_id}_{os.urandom(4).hex()}.xlsx'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        df.to_excel(file_path, index=False)
        return send_file(file_path, as_attachment=True, download_name=f'相似匹配结果.xlsx')
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'导出失败：{str(e)}'})

# 5. 买卖点预测接口
@app.route('/predict_buy_sell', methods=['POST'])
def predict_buy_sell_api():
    try:
        ts_code = request.form.get('ts_code')
        model_type = request.form.get('model_type', 'rf')
        data = predict_buy_sell(ts_code, model_type)
        return jsonify({'code': 200, 'data': data})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'预测失败：{str(e)}'})

# 6. 策略回测接口
@app.route('/backtest_strategy', methods=['POST'])
def backtest_strategy_api():
    try:
        ts_code = request.form.get('ts_code')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        strategy_type = request.form.get('strategy_type', 'trend')
        data = backtest_strategy(ts_code, start_date, end_date, strategy_type)
        return jsonify({'code': 200, 'data': data})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'回测失败：{str(e)}'})

@app.route('/get_industries', methods=['GET'])
def get_industries_api():
    try:
        # 调用原有的get_industry_list函数
        data = get_industry_list()
        return jsonify({'code': 200, 'data': data})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'获取失败：{str(e)}'})
# ---------------------- 修复的接口 ----------------------
# 7. 获取所有股票（兼容前端老接口）
@app.route('/get_stocks', methods=['GET'])
def get_stocks_api():
    try:
        data = get_stock_list()
        return jsonify({'code': 200, 'data': data})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'获取失败：{str(e)}'})

# 8. 根据ID获取单个模板
@app.route('/get_pattern_by_id', methods=['GET'])
def get_pattern_by_id_api():
    try:
        pattern_id = request.args.get('id')
        pattern = get_pattern_by_id(pattern_id)
        if pattern:
            return jsonify({'code': 200, 'data': pattern})
        else:
            return jsonify({'code': 404, 'msg': '模板不存在'})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'获取失败：{str(e)}'})

# 9. 匹配接口（兼容老接口）
@app.route('/match', methods=['POST'])
def match_api_old():
    try:
        pattern_id = request.form.get('pattern_id')
        data = match_pattern(pattern_id, {})
        return jsonify({'code': 200, 'data': data})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'匹配失败：{str(e)}'})

# 10. 健康检查接口
@app.route('/api/status', methods=['GET'])
@app.route('/status', methods=['GET'])
def status_check():
    return jsonify({
        'code': 200,
        'status': 'running',
        'service': '股票智能分析系统',
        'version': '1.0.0',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'endpoints': {
            'data_crawl': '/crawl_data',
            'stock_list': '/get_stock_list',
            'pattern_management': '/get_patterns',
            'pattern_matching': '/match_pattern',
            'prediction': '/predict_buy_sell',
            'backtest': '/backtest_strategy'
        }
    })

@app.route('/health')
def health_check():
    return 'OK', 200

# ---------------------- 启动配置 ----------------------
if __name__ == "__main__":
    # 开发环境：app.run(debug=True, host='0.0.0.0', port=5000)
    # 生产环境
    print("服务器启动：http://127.0.0.1:5000")
    serve(app, host='0.0.0.0', port=5000)