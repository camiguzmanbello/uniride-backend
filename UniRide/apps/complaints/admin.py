from django.contrib import admin
from .models import Complaint, ComplaintType, ComplaintStatus

@admin.register(ComplaintType)
class ComplaintTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(ComplaintStatus)
class ComplaintStatusAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('reporter_id', 'type_id', 'status_id', 'created_at', 'admin_id')
    search_fields = ('description', 'reporter_id__email')
    list_filter = ('status_id', 'type_id')
