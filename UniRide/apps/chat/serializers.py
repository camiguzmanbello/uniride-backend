from rest_framework import serializers
from django.db.models import Q
from .models import Chat, Message
from apps.trips.models import Publication
from apps.trips.services.trip_flow import create_interest
from apps.users.serializer import UserSerializer

class SimpleUserSerializer(serializers.ModelSerializer):
    """Serializer ligero para mostrar info básica de usuario en el chat"""
    class Meta:
        from apps.users.models import User
        model = User
        fields = ['id', 'name', 'email', 'profile_image']
        ref_name = "ChatSimpleUser"

class MessageSerializer(serializers.ModelSerializer):
    sender = SimpleUserSerializer(source='sender_id', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'content', 'sender', 'sent_at', 'is_read', 'is_quick_message']
        read_only_fields = ['id', 'sender', 'sent_at', 'is_read']

class ChatListSerializer(serializers.ModelSerializer):
    passenger = SimpleUserSerializer(read_only=True)
    driver = SimpleUserSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    publication_title = serializers.SerializerMethodField()
    trip_passenger_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Chat
        fields = ['id', 'publication', 'publication_title', 'passenger', 'driver', 'is_active', 'created_at', 'closed_at', 'last_message', 'trip_passenger', 'trip_passenger_status']

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-sent_at').first()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None
    
    def get_publication_title(self, obj):
        return str(obj.publication)

    def get_trip_passenger_status(self, obj):
        if obj.trip_passenger:
            return obj.trip_passenger.status_id.name
        return None

class ChatCreateSerializer(serializers.ModelSerializer):
    publication_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Chat
        fields = ['id', 'publication_id']

    def create(self, validated_data):
        request = self.context.get('request')
        publication_id = validated_data.get('publication_id')
        
        # Recuperar publicación para determinar roles
        try:
            publication = Publication.objects.get(id=publication_id)
        except Publication.DoesNotExist:
             raise serializers.ValidationError("Publicación no encontrada.")
             
        pub_type = publication.type_id.name.lower()
        
        try:
            if 'oferta' in pub_type:
                 # El usuario actual es el pasajero interesado
                 result = create_interest(publication_id, request.user)
            elif 'solicitud' in pub_type:
                 # El usuario actual es el conductor interesado
                 # El pasajero es el dueño de la publicación
                 result = create_interest(publication_id, publication.user_id, driver_user=request.user)
            else:
                 raise serializers.ValidationError("Tipo de publicación no soportado.")
                 
            return result['chat']
            
        except Exception as e:
            # Re-raise as ValidationError if it's not already
            if hasattr(e, 'detail'):
                raise e
            raise serializers.ValidationError(str(e))
