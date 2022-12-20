from django.db import models
from authentication.models import BaseModel,CustomUser
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
# Create your models here.

class Notifications(BaseModel):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    notification = models.CharField(max_length=1000)
    is_seen = models.BooleanField(default=False)


    def save(self, *args, **kwargs):
        channel_layer = get_channel_layer()
        notification = Notifications.objects.filter(is_seen=False).count()
        data = {'count':notification,'current_notification':self.notification}
        async_to_sync(channel_layer.group_send)(
            f'test_consumer_group-{self.user.id}', {
                'type': 'send_notification',
                'value': json.dumps(data)
            }
        )
        super(Notifications, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.notification}'

    class Meta:
        verbose_name_plural = 'Notifications'