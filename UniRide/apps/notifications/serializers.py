from rest_framework import serializers
from .models import Notification, UserDevice

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'type', 'title', 'message', 'is_read', 'metadata', 'created_at']
        read_only_fields = ['id', 'type', 'title', 'message', 'metadata', 'created_at']

class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = ['token', 'platform']
