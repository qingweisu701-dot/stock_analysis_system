# config.py
import os
from pathlib import Path

# 项目根目录（根据实际项目结构调整）
BASE_DIR = Path(__file__).resolve().parent  # 假设 config.py 在项目根目录下
# 若 config.py 在子目录（如 settings/），可使用：
# BASE_DIR = Path(__file__).resolve().parent.parent

# ==================== 基础配置 ====================
# 数据库路径
DB_PATH = "db/stock.db"

# Tushare Token（替换为自己的Token，注册地址：https://tushare.pro/）
TUSHARE_TOKEN = "9dafb0670f8fe189483519136b028bbba0732211772b0334e7c74852"

# 上传文件目录
UPLOAD_FOLDER = "uploads"

# 时间配置（默认采集最近180天数据）
DEFAULT_DATA_DAYS = 180

#项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))