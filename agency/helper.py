import base64
from sendgrid.helpers.mail import Mail, Email, To, Content
from twilio.rest import Client
from django.conf import settings
from skpy import Skype
from sendgrid.helpers.mail import Mail, Email, To, Content
from adifect.settings import SEND_GRID_API_key, FRONTEND_SITE_URL, LOGO_122_SERVER_PATH, BACKEND_SITE_URL
from adifect.settings import TWILIO_NUMBER
import sendgrid
from django.conf import settings


class StringEncoder:
    "This is  encoder decoder class"

    def encode(self, value):
        byte_msg = str(value).encode('ascii')
        base64_value = base64.b64encode(byte_msg)
        idDecoded = base64_value.decode('ascii')
        idDecoded = idDecoded.strip()
        return idDecoded

    def decode(self, value):
        byte_msg = value.encode('ascii')
        base64_val = base64.b64decode(byte_msg)
        encoded_id = base64_val.decode('ascii')
        return encoded_id


def send_text_message(body, twilio_number, to):
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    try:
        client = Client(account_sid, auth_token)

        message = client.messages.create(
            body=body,
            from_=twilio_number,
            to=to
        )
        return True
    except Exception as e:
        print(e)
        return False


def send_skype_message(receiver, message):
    try:
        skype = Skype(settings.SKYPE_USERNAME, settings.SKYPE_PASSWORD)
        send = skype.contacts.contact(receiver).chat
        send.sendMsg(str(message))
        return True
    except Exception as e:
        print(e)
        return False


def send_email(from_email, to_email, subject, content):
    try:
        sg = sendgrid.SendGridAPIClient(api_key=SEND_GRID_API_key)
        mail = Mail(from_email, to_email, subject, content)
        mail_json = mail.get()
        response = sg.client.mail.send.post(request_body=mail_json)
        return True
    except Exception as e:
        print(e)
        return False


def send_whatsapp_message(twilio_number_whatsapp, body, to):
    account_sid = settings.TWILIO_ACCOUNT_SID2
    auth_token = settings.TWILIO_AUTH_TOKEN2
    try:
        client = Client(account_sid, auth_token)

        message = client.messages.create(
            from_=twilio_number_whatsapp,
            body=body,
            to='whatsapp:' + str(to)
        )
        return True
    except Exception as e:
        print(e)
        return False
