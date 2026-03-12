from rest_framework import permissions

class IsSelfOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Permite si es el mismo usuario o si es admin
        return obj == request.user or request.user.is_staff