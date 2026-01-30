import pymysql
pymysql.install_as_MySQLdb()

# 这将确保Celery app在Django启动时被初始化
from .celery import app as celery_app

__all__ = ('celery_app',)