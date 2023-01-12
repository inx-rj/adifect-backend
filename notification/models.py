from django.db import models
from authentication.models import BaseModel, CustomUser
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import asyncio
import websockets
from django.db.models.signals import post_save
from django.dispatch import receiver


# Create your models here.

async def send_notification(id, data_value):
    # async with websockets.connect(f'wss://dev-ws.adifect.com/ws/notifications/{id}/') as websocket:
    async with websockets.connect(f'ws://122.160.74.251:8018/ws/notifications/{id}/') as websocket:
        await websocket.send(data_value)
        await websocket.recv()


class Notifications(BaseModel):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    notification = models.CharField(max_length=1000)
    is_seen = models.BooleanField(default=False)
    

    # def save(self, *args, **kwargs):
    # notification_count = Notifications.objects.filter(is_seen=False,user=self.user).count()
    # data = '{"text":{"count":'+str(notification_count)+', "current_notification": "'+str(self.notification)+'"}}'
    # # data = '{"type": "send_notification","text":{"count": "150", "current_notification": "yes tessting"}}'
    # asyncio.run(send_notification(str(self.user.id),data))
    # asyncio.run(send_notification("2",data))
    # super(Notifications, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.notification}'

    class Meta:
        verbose_name_plural = 'Notifications'


@receiver(post_save, sender=Notifications)
def create_realtime_Notification(sender, instance, created, **kwargs):
    if created:
        notification_count = Notifications.objects.filter(is_seen=False, user=instance.user).count()
        data = '{"text":{"count":' + str(notification_count) + ', "current_notification": "' + str(
            instance.notification) + '"}}'
        asyncio.run(send_notification(str(instance.user.id), data))
        return True
    return False


class TestMedia(BaseModel):
    media = models.FileField(upload_to="uploded/", blank=True)
    title = models.CharField(max_length=1000, blank=True, null=True)
    is_done = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'TestMedia'
