import os
from channels.routing import ProtocolTypeRouter,URLRouter
from channels.auth import AuthMiddlewareStack
from notification import consumers

from django.urls import re_path,path
from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adifect.settings')
# import notification.routing
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket":AuthMiddlewareStack(
URLRouter(

[path('stories/notification_testing/<int:pk>/',consumers.NotificationConsumer.as_asgi())]
))


})