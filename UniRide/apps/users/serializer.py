from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .utils.validate_password import validar_password_y_confirmacion
from django.contrib.auth import get_user_model
from .utils.validations import validate_phone_number, validate_email, validate_name

User = get_user_model()
class CustomTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['rol'] = user.role_id.id
        return token

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)

#Serializers Cambios en el perfil 
class CambiarPasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password= serializers.CharField()

    def validate(self, data):
        return validar_password_y_confirmacion(data, context_user=self.context['request'].user)
    
class EditarPerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'phone']
        extra_kwargs = {
            'name': {'required': False},
            'phone': {'required': False},
        }

    def validate_phone(self, value):
        value = validate_phone_number(value)
        
        user_qs = User.objects.exclude(pk=self.instance.pk) if self.instance else User.objects.all()
        if user_qs.filter(phone=value).exists():
            raise serializers.ValidationError("Ese número de teléfono ya está en uso.")
        return value

    def validate_name(self, value):
        return validate_name(value)
   
class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        return validar_password_y_confirmacion(data, context_user=self.instance or None)