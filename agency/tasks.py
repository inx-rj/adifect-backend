import random
from celery import shared_task
from helper.helper import send_email
from adifect.settings import SEND_GRID_FROM_EMAIL
from agency.views import send_reminder_email

@shared_task(name="approver_reminder_email")
def mul():
    # Celery recognizes this as the `multiple_two_numbers` task
    send_reminder_email()
    return True
