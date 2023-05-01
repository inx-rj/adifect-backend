import os
from datetime import timedelta

from celery import Celery
from django.conf import settings


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adifect.settings')

app = Celery('adifect')
# app.conf.enable_utc = False

# app.conf.update(timezone='Asia/Kolkata')

app.config_from_object(settings, namespace='CELERY')


# Celery Schedules - https://docs.celeryproject.org/en/stable/reference/celery.schedules.html

app.conf.beat_schedule = {
    'reminder-email-every-1-minute': {
        'task': 'approver_reminder_email',
        'schedule': timedelta(hours=3),
        # 'args': (16, 16)
    },
    'community-data-entry-every-1-hour': {
        'task': 'community_data_entry',
        'schedule':  timedelta(days=1)
    },
}

app.autodiscover_tasks()
