from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import *
from rest_framework.viewsets import ModelViewSet
from django.db.models import Q
from rest_framework.decorators import action
from apps.trips.services.trip_flow import accept_passenger


class PublicationTypeViewSet(ModelViewSet):

    permission_classes = [permissions.AllowAny]

    queryset = PublicationType.objects.all()
    serializer_class = PublicationTypeSerializer


class PublicationViewSet(ModelViewSet):

    permission_classes = [permissions.AllowAny]

    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer

    #para que al crear una publicacion se asigne el user logueado
    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user)
    

class TripPassengerViewSet(ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TripPassengerSerializer
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return TripPassenger.objects.none()
        return TripPassenger.objects.filter(
            Q(passenger_id=user) | Q(trip_id__driver_id=user)
        )

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        try:
            tp = accept_passenger(pk, request.user)
            return Response(TripPassengerSerializer(tp).data)
        except Exception as e:
            status_code = status.HTTP_400_BAD_REQUEST
            detail = str(e)
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            if hasattr(e, 'detail'):
                detail = e.detail
            return Response({"detail": detail}, status=status_code)

class TripStatusViewSet(ModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = TripStatus.objects.all()
    serializer_class = TripStatusSerializer


class TripPassengerStatusViewSet(ModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = TripPassengerStatus.objects.all()
    serializer_class = TripPassengerStatusSerializer


