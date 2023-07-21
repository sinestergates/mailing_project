import os
import time
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mailing.settings')
app = Celery('mailing')
app.config_from_object('django.conf:settings')
app.conf.broker_url = settings.CELERY_BROKER_URL
app.autodiscover_tasks()


@app.task()
def task_test():
    time.sleep(20)
    print('11111111121111111111111111111111111111')