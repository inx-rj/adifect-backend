import datetime
import logging
import os
import random
import string
import requests

from community.models import Story


logger = logging.getLogger('django')


def get_purl():
    while True:
        p_url = ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=8))
        if not Story.objects.filter(p_url=p_url).exists():
            return p_url


def date_format(input_date):
    date_obj = datetime.datetime.strptime(input_date, "%Y-%m-%dT%H:%M:%SZ")
    return date_obj.strftime("%Y-%m-%d")


def validate_client_id_opnsesame(client_id, api_key):
    """Check if the client id provided is valid or not."""

    base_url = os.environ.get("OPNSESAME_API_URL", "")
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Accept': 'application/json',
        'Authorization': f'Token {api_key}'
    }
    logger.info(f"-------{base_url}organizations/{client_id}")
    resp = requests.request("GET", f"{base_url}organizations/{client_id}", headers=headers)
    logger.info(f"Client id check for audiences ## {resp.status_code}")
    return resp.status_code == 200
