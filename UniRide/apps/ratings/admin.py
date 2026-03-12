from django.contrib import admin
from .models import Rating

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('reviewer_id', 'reviewed_id', 'trip_id', 'stars', 'created_at')
    search_fields = ('reviewer_id__email', 'reviewed_id__email', 'comment')
    list_filter = ('stars',)
