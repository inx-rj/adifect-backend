from django.db import models
from authentication.models import BaseModel, CustomUser
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import asyncio
import websockets


# Create your models here.

async def send_notification(id,data_value):
    async with websockets.connect(f'wss://dev-ws.adifect.com/ws/notifications/{id}/') as websocket:
        await websocket.send(data_value)
        await websocket.recv()


class Notifications(BaseModel):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    notification = models.CharField(max_length=1000)
    is_seen = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        notification_count = Notifications.objects.filter(is_seen=False).count()
        data = '{"text":{"count":'+str(notification_count)+', "current_notification": "'+str(self.notification)+'"}}'
        asyncio.run(send_notification(self.user.id,data))
        super(Notifications, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.notification}'

    class Meta:
        verbose_name_plural = 'Notifications'


class TestMedia(BaseModel):
    media = models.FileField(upload_to="uploded/", blank=True)
    title = models.CharField(max_length=1000, blank=True, null=True)
    is_done = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'TestMedia'
