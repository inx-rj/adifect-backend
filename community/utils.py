import datetime
import random
import string

from community.models import Story


def get_purl():
    while True:
        p_url = ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=8))
        if not Story.objects.filter(p_url=p_url).exists():
            return p_url


def date_format(input_date):
    date_obj = datetime.datetime.strptime(input_date, "%Y-%m-%dT%H:%M:%SZ")
    return date_obj.strftime("%Y-%m-%d")
