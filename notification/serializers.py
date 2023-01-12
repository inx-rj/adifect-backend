from rest_framework import serializers
from .models import Notifications, TestMedia



class NotificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = '__all__'


class TestMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestMedia
        fields = '__all__'
