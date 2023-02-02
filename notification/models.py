from django.db import models
from authentication.models import BaseModel, CustomUser
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import asyncio
import websockets
from django.db.models.signals import post_save
from django.dispatch import receiver
from agency.models import Company

# Create your models here.

async def send_notification(id, data_value):
    # async with websockets.connect(f'wss://dev-ws.adifect.com/ws/notifications/{id}/') as websocket:
    async with websockets.connect(f'ws://122.160.74.251:8018/ws/notifications/{id}/') as websocket:
        await websocket.send(data_value)
        await websocket.recv()


class Notifications(BaseModel):
    TYPE_CHOICES = (
        ("job_edited", "job_edited"),
        ("job_proposal", "job_proposal"),
        ("job_submit_work", "job_submit_work"),
        ("job_work_approver", "job_work_approver"),
        ("job_completed", "job_completed"),
        ("in_house_assigned", "in_house_assigned"),
        ("invite_accepted", "invite_accepted"),

    )

    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    notification = models.CharField(max_length=1000)
    is_seen = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=60,
                                         choices=TYPE_CHOICES,default='job_proposal')
    redirect_id = models.IntegerField(blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name="company_notifications")


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
            instance.notification) +'", "notification_type":"'+str(instance.notification_type)+ '", "redirect_id": "' + str(
            instance.redirect_id)+'"}}'
        asyncio.run(send_notification(str(instance.user.id), data))
        return True
    return False


class TestMedia(BaseModel):
    media = models.FileField(upload_to="uploded/", blank=True)
    title = models.CharField(max_length=1000, blank=True, null=True)
    is_done = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'TestMedia'
