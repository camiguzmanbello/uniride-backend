from django.contrib import admin
from .models import Chat, Message

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'publication', 'passenger', 'driver', 'is_active', 'created_at')
    list_filter = ('is_active',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'sender_id', 'content', 'sent_at', 'is_read')
    search_fields = ('content', 'sender_id__email')
    list_filter = ('is_read',)
