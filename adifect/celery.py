import os
from datetime import timedelta

from celery import Celery
from celery.schedules import crontab
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
    'community-data-entry': {
        'task': 'community_data_entry',
        'schedule': timedelta(days=1)
    },
    'community-daily-story-updates': {
        'task': 'daily_story_updates',
        'schedule': timedelta(hours=1)
    },
    'audience-daily-community-updates': {
        'task': 'daily_audience_community_updates',
        'schedule': timedelta(hours=3)
    },
    'community-settings-story-fetch': {
        'task': 'story_community_settings',
        'schedule': timedelta(minutes=20)
    }
}

app.autodiscover_tasks()
