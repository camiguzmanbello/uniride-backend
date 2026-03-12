from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Role, PendingUser, VehicleType, Vehicle, UserSuspension, AuditLog

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'name', 'phone', 'role_id', 'is_verified', 'is_suspended', 'is_active')
    search_fields = ('email', 'name', 'phone')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'phone', 'profile_image', 'first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Custom fields', {'fields': ('role_id', 'is_verified', 'is_suspended')}),
    )

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(PendingUser)
class PendingUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'phone', 'code', 'expires_at', 'registrado_por')
    search_fields = ('email', 'name', 'code')

@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate', 'brand', 'model', 'color', 'user_id', 'type_id', 'is_active')
    search_fields = ('plate', 'brand', 'user_id__email')
    list_filter = ('type_id', 'is_active')

@admin.register(UserSuspension)
class UserSuspensionAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'reason', 'start_date', 'end_date', 'is_permanent', 'admin_id')
    search_fields = ('user_id__email', 'reason')
    list_filter = ('is_permanent',)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'actor', 'action', 'target_user')
    search_fields = ('actor__email', 'action')
    list_filter = ('action',)
