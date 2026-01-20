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


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """调试任务"""
    print(f"Request: {self.request!r}")
