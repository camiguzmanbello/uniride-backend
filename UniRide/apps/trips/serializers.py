from rest_framework import serializers
from apps.trips.models import *

class PublicationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicationType
        fields = ['id', 'name']
        read_only_fields = ['id']

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

class TripPassengerSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='status_id.name', read_only=True)
    passenger_name = serializers.CharField(source='passenger_id.name', read_only=True)
    
    class Meta:
        model = TripPassenger
        fields = ['id', 'trip_id', 'passenger_id', 'passenger_name', 'seats_reserved', 'status', 'joined_at', 'finalized_at']
        read_only_fields = ['id', 'trip_id', 'passenger_id', 'status', 'joined_at', 'finalized_at']

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
