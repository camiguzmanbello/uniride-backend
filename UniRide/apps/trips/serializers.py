from rest_framework import serializers
from django.utils import timezone
from apps.trips.models import *
from apps.trips.services.trip_flow import user_has_active_trip

class PublicationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicationType
        fields = ['id', 'name']
        read_only_fields = ['id']

class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        from apps.users.models import User
        model = User
        fields = ['id', 'name', 'email', 'profile_image', 'phone']
        ref_name = "TripSimpleUser"

class PublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publication
        fields = [
            'id', 'user_id', 'type_id', 'vehicle_id', 'departure_place', 'destination',
            'departure_datetime', 'lat_departure_place', 'lon_departure_place',
            'lat_destination', 'lon_destination', 'available_seats', 'description',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'user_id']

    def validate(self, attrs):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            
            # Determinar si la publicación resultante estará activa
            is_active_new = attrs.get('is_active', True)
            if self.instance and 'is_active' not in attrs:
                is_active_new = self.instance.is_active
                
            if is_active_new:
                # 0. Validar que la fecha de salida no sea en el pasado
                departure_datetime = attrs.get('departure_datetime')
                if not departure_datetime and self.instance:
                    departure_datetime = self.instance.departure_datetime
                
                if departure_datetime and departure_datetime < timezone.now():
                    raise serializers.ValidationError("No puedes crear o activar una publicación con una fecha de viaje pasada.")

                # 1. Validar publicación activa única
                existing_active = Publication.objects.filter(user_id=user, is_active=True)
                if self.instance:
                    existing_active = existing_active.exclude(pk=self.instance.pk)
                
                if existing_active.exists():
                    raise serializers.ValidationError("Ya tienes una publicación activa. Debes finalizarla o cancelarla antes de crear una nueva.")
                    
                # 2. Validar viaje activo único
                if user_has_active_trip(user):
                    raise serializers.ValidationError("Ya tienes un viaje en curso. No puedes crear una publicación hasta que finalice.")
        
        # 3. Validar vehículo según tipo de publicación
        type_obj = attrs.get('type_id')
        vehicle_obj = attrs.get('vehicle_id')
        
        if type_obj:
            type_name = type_obj.name.lower()
            if 'oferta' in type_name and not vehicle_obj:
                raise serializers.ValidationError({"vehicle_id": "Para publicar una oferta es obligatorio seleccionar un vehículo."})
            if 'solicitud' in type_name and vehicle_obj:
                # Opcional: Podríamos forzar vehicle_id=None aquí, o lanzar error.
                # Para ser estrictos y evitar confusión:
                attrs['vehicle_id'] = None
                 
        return attrs

class TripPassengerSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='status_id.name', read_only=True)
    passenger = SimpleUserSerializer(source='passenger_id', read_only=True)
    
    class Meta:
        model = TripPassenger
        fields = ['id', 'trip_id', 'passenger', 'seats_reserved', 'status', 'joined_at', 'finalized_at']
        read_only_fields = ['id', 'trip_id', 'passenger', 'status', 'joined_at', 'finalized_at']

class InterestSerializer(serializers.Serializer):
    publication_id = serializers.IntegerField()
    seats_reserved = serializers.IntegerField(default=1)

class TripStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripStatus
        fields = ['id', 'name']
        read_only_fields = ['id']

class TripPassengerStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripPassengerStatus
        fields = ['id', 'name']
        read_only_fields = ['id']

class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = '__all__'
        read_only_fields = ['id', 'driver_id', 'publication_id', 'status_id', 'created_at', 'finalized_at']

class TripHistorySerializer(serializers.ModelSerializer):
    publication = PublicationSerializer(source='publication_id', read_only=True)
    status = serializers.CharField(source='status_id.name', read_only=True)
    driver_name = serializers.CharField(source='driver_id.name', read_only=True)
    role = serializers.SerializerMethodField()
    canceled_by_name = serializers.CharField(source='canceled_by.name', read_only=True, allow_null=True)
    user_cancellation_confirmed = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            'id', 'status', 'role', 'driver_name', 'publication', 
            'created_at', 'finalized_at', 'auto_finalized',
            'cancel_reason', 'canceled_by_name', 'user_cancellation_confirmed'
        ]
    
    def get_role(self, obj):
        user = self.context.get('request').user
        if obj.driver_id == user:
            return 'Conductor'
        return 'Pasajero'

    def get_user_cancellation_confirmed(self, obj):
        user = self.context.get('request').user
        if obj.driver_id == user:
            return obj.driver_cancellation_ack
        
        # Si es pasajero, buscamos su registro
        passenger_record = obj.passengers.filter(passenger_id=user).first()
        if passenger_record:
            return passenger_record.cancellation_ack
        return False

class CancelTripSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True, max_length=500)
