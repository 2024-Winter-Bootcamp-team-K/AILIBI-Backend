from __future__ import absolute_import, unicode_literals

# Celery를 import하여 Django가 초기화될 때 Celery를 함께 초기화
from .celery import app as celery_app

__all__ = ('celery_app',)