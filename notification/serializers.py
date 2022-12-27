from rest_framework import serializers
from .models import Notifications, TestMedia



class NotificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = '__all__'


class TestMediaSerializer(serializers.ModelSerializer):
    sample_files = serializers.FileField(allow_empty_file=True, required=False)
    class Meta:
        model = TestMedia
        fields = '__all__'
