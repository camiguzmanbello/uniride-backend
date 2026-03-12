from django.contrib import admin
from .models import Notification, UserDevice

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'type', 'title', 'is_read', 'created_at')
    search_fields = ('recipient__email', 'title', 'message')
    list_filter = ('type', 'is_read')

@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'platform', 'is_active', 'last_synced')
    search_fields = ('user__email',)
    list_filter = ('platform', 'is_active')
