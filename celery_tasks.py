import celery
from data_crawl import crawl_stock_price, calculate_tech_index
from config import BASE_DIR

# 配置Celery
app = celery.Celery(
    'stock_tasks',
    broker='redis://localhost:6379/0',  # Redis地址
    backend='redis://localhost:6379/0'
)

# 定时任务：每小时更新行情+技术指标
@app.task
def update_stock_data():
    crawl_stock_price()  # 增量更新行情数据
    calculate_tech_index()  # 重新计算技术指标
    print("数据已定时更新")

# 配置定时任务（Celery Beat）
app.conf.beat_schedule = {
    'update-stock-every-hour': {
        'task': 'celery_tasks.update_stock_data',
        'schedule': 3600.0,  # 每3600秒（1小时）执行一次
    },
}