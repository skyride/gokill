from __future__ import absolute_import
from celery import Celery

app = Celery('app')
app.config_from_object('settings')
app.autodiscover_tasks([
    'hydration'
])