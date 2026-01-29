from rest_framework import permissions

class IsChatParticipant(permissions.BasePermission):
    """
    Permite el acceso solo si el usuario es pasajero o conductor del chat.
    """
    def has_object_permission(self, request, view, obj):
        return request.user == obj.passenger or request.user == obj.driver
