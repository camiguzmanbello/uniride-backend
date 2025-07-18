from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from apps.users.models import User, Role, PendingUser, Vehicle, VehicleType

class CustomTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['rol'] = user.role_id.id
        return token
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name']
        read_only_fields = ['id']

class PendingUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingUser
        fields = ['id', 'name', 'email', 'phone', 'password', 'role_id', 'profile_image', 'code', 'expires_at', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True},
            'code': {'read_only': True},
            'expires_at': {'read_only': True},
            'created_at': {'read_only': True},
            'role_id': {'required': False, 'allow_null': True}
        }

    def validate_email(self, value):
        dominio = "@ucundinamarca.edu.co"
        if not value.lower().endswith(dominio):
            raise serializers.ValidationError("Debes usar un correo institucional de la Universidad de Cundinamarca.")
        return value
    
    def create(self, validated_data):
        if 'role_id' not in validated_data or validated_data['role_id'] is None:
            validated_data['role_id'] = Role.objects.get(name='Usuario')
        pendinguser = PendingUser.objects.create(**validated_data)
        return pendinguser
        

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone', 'password', 'role_id', 'profile_image', 'created_at', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True},
            'role_id': {'required': False, 'allow_null': True},
            'created_at': {'read_only': True},
            'is_active': {'read_only': True}
        }

    def validate_email(self, value):
        dominio = "@ucundinamarca.edu.co"
        if not value.lower().endswith(dominio):
            raise serializers.ValidationError("Debes usar un correo institucional de la Universidad de Cundinamarca.")
        return value    
    
    def create(self, validated_data):
        if 'role_id' not in validated_data or validated_data['role_id'] is None:
            validated_data['role_id'] = Role.objects.get(name='Usuario')
        # Generar username si no viene
        if 'username' not in validated_data or not validated_data['username']:
            validated_data['username'] = validated_data['email']
        user = User.objects.create_user(**validated_data)
        return user
    
class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = ['id', 'name']
        read_only_fields = ['id']
   
class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'
        extra_kwargs = {
            'user_id': {'read_only': True},
            'type_id': {'required': True}
        }

class VerifyCodeSerializer(serializers.Serializer):
    code = serializers.CharField()

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=6)

