from rest_framework import viewsets, mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification, UserDevice
from .serializers import NotificationSerializer, UserDeviceSerializer

class NotificationViewSet(mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=['patch'])
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})

class DeviceViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserDeviceSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        platform = serializer.validated_data.get('platform', 'web')
        
        # Idempotent registration
        device, created = UserDevice.objects.update_or_create(
            user=request.user,
            token=token,
            defaults={
                'platform': platform,
                'is_active': True
            }
        )
        
        # If it existed but was updated (e.g. re-activated), update_or_create handles it via defaults
        # But we also want to update last_synced if it wasn't created
        if not created:
            device.save() # Updates auto_now field last_synced
            
        return Response({'status': 'registered', 'device_id': device.id}, status=status.HTTP_201_CREATED)
