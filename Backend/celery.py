
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# Django의 settings 모듈에서 기본 설정을 가져옵니다.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')

app = Celery('Backend')

# Django의 설정을 Celery에 적용합니다.
app.config_from_object('django.conf:settings', namespace='CELERY')

# 자동으로 task를 찾습니다.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')