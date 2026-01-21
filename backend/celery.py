"""
Celery配置文件
"""

import os

from celery import Celery

# 设置默认的Django settings模块
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")

# 从Django settings加载配置
app.config_from_object("django.conf:settings", namespace="CELERY")

# 自动发现所有已安装应用的tasks.py
app.autodiscover_tasks()

# ===== MinerU 任务并发控制 =====
# 限制 worker 并发数为 1，避免 MinerU 服务过载
app.conf.worker_concurrency = 1


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """调试任务"""
    print(f"Request: {self.request!r}")
