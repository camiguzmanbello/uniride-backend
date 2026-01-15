from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from apps.users.models import User, Role, PendingUser, Vehicle, VehicleType
from .utils.validate_password import validar_password_y_confirmacion
from django.contrib.auth import get_user_model
from .utils.validations import validate_phone_number, validate_email, validate_name
from django.utils.translation import gettext_lazy as _
User = get_user_model()


class CustomTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        return token


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        return value.lower()

# Serializers Cambios en el perfil


class CambiarPasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):

        validar_password_y_confirmacion(
            password1=data["new_password"],
            password2=data["confirm_password"],
            context_user=self.context['request'].user
        )
        
        return data


class EditarPerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'phone']
        extra_kwargs = {
            'name': {'required': False},
            'phone': {'required': False, 'validators': []},
        }

    def validate_phone(self, value):
        value = validate_phone_number(value)

        # Validar duplicados en User
        user_qs = User.objects.exclude(
            pk=self.instance.pk) if self.instance else User.objects.all()
        if user_qs.filter(phone=value).exists():
            raise serializers.ValidationError(
                "Ese número de teléfono ya está en uso por otro usuario.")

        # Validar duplicados en PendingUser
        if PendingUser.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "Ese número de teléfono ya está en uso por un usuario pendiente.")

        return value

    def validate_name(self, value):
        return validate_name(value)


class PendingAdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingUser
        fields = ['name', 'email', 'phone']

    def validate_name(self, value):
        return validate_name(value)

    def validate_phone(self, value):
        return validate_phone_number(value)

    def validate_email(self, value):
        return validate_email(value)


class ConfirmAdminSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    def validate(self, data):

        # Esto lanza serializers.ValidationError en caso de fallo
        validated_password = validar_password_y_confirmacion(
            password1=data["password"],
            password2=data["confirm_password"],
            context_user=self.context['request'].user
        )

        data["password"] = validated_password  
        return data

class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'role_id']


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name']
        read_only_fields = ['id']


class PendingUserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = PendingUser
        fields = [
            'id', 'name', 'email', 'phone', 'password', 'confirm_password',
            'role_id', 'profile_image', 'code', 'expires_at', 'created_at'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'code': {'read_only': True},
            'expires_at': {'read_only': True},
            'created_at': {'read_only': True},
            'role_id': {'required': False, 'allow_null': True},
            'profile_image': {'required': False, 'allow_null': True}
        }

    def validate_email(self, value):
        dominio = "@ucundinamarca.edu.co"
        if not value.lower().endswith(dominio):
            raise serializers.ValidationError(
                "Debes usar un correo institucional de la Universidad de Cundinamarca.")
        return value

    def validate_phone(self, value):
        return validate_phone_number(value)

    def validate(self, data):
        """Validar que las contraseñas coincidan."""
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError(
                {"confirm_password": "Las contraseñas no coinciden."})
        return data

    def create(self, validated_data):

        # Eliminar antes de crear la instancia
        validated_data.pop('confirm_password')

        # Asignar rol por defecto si no se proporciona
        if 'role_id' not in validated_data or validated_data['role_id'] is None:
            validated_data['role_id'] = Role.objects.get(name='Usuario')



        # Crear el PendingUser
        pendinguser = PendingUser.objects.create(**validated_data)

        return pendinguser
        


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone', 'password',
                  'role_id', 'profile_image', 'created_at', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True},
            'role_id': {'required': False, 'allow_null': True},
            'created_at': {'read_only': True},
            'is_active': {'read_only': True}
        }

    def validate_email(self, value):
        dominio = "@ucundinamarca.edu.co"
        if not value.lower().endswith(dominio):
            raise serializers.ValidationError(
                "Debes usar un correo institucional de la Universidad de Cundinamarca.")
        return value

    def create(self, validated_data):

       # Asignar rol por defecto
        validated_data.setdefault(
            'role_id', Role.objects.get(name='Usuario')
        )

        # Generar username si no viene
        validated_data.setdefault('username', validated_data['email'])

        # Guardar contraseña
        raw_password = validated_data.pop("password")


        # Crear usuario NORMAL, no create_user
        user = User.objects.create(**validated_data)
        user.set_password(raw_password)
        user.save()

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
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Validar que las contraseñas coincidan."""
        if data.get('new_password') != data.get('confirm_password'):
            raise serializers.ValidationError(
                {"confirm_password": "Las contraseñas no coinciden."})
        return data


class ResendNewVerificationCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
