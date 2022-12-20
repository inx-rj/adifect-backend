from channels.generic.websocket import WebsocketConsumer,AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync,sync_to_async
from channels.layers import get_channel_layer
from notification.models import Notifications
from authentication.models import CustomUser
import json




@database_sync_to_async
def get_user(user_id):
    try:
        return CustomUser.objects.get(id=user_id)
    except:
        return ''
@database_sync_to_async
def create_notification(receiver,typeof="task_created",status="unread"):
    notification_to_create=Notifications.objects.create(user=receiver,notification=typeof)
    # print('I am here to help')
    return (notification_to_create.user.username,notification_to_create.notification)

class NotificationConsumer(AsyncWebsocketConsumer):

    async def websocket_connect(self,event=None):
            print(self.scope["url_route"]["kwargs"]["pk"])
            # print(self.scope)
            await self.accept()
            await self.send(json.dumps({
                        "type":"websocket.send",
                        "text":"hello world"
                    }))
            self.room_name = f'test_consumer-{self.scope["url_route"]["kwargs"]["pk"]}'
            self.room_group_name = f'test_consumer_group-{self.scope["url_route"]["kwargs"]["pk"]}'
            await self.channel_layer.group_add(self.room_group_name,self.channel_name)
            self.send({
                "type":"websocket.send",
                "text":"room made"
            })

    async def websocket_receive(self,event):
            # print(event)
            print('second')
            data_to_get=json.loads(event['text'])
            user_to_get=await get_user(int(data_to_get))
            # print(user_to_get)
            get_of=await create_notification(user_to_get)
            self.room_group_name=f'test_consumer_group-{self.scope["url_route"]["kwargs"]["pk"]}'
            channel_layer=get_channel_layer()
            await (channel_layer.group_send)(
                self.room_group_name,
                {
                    "type":"send_notification",
                    "value":json.dumps(get_of)
                }
            )
            # print('receive',event)

    async def websocket_disconnect(self,event):
            print('disconnect',event)

    async def send_notification(self,event):
            print('third')
            await self.send(json.dumps({
                "type":"websocket.send",
                "data":event
            }))

