from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from apps.ratings.models import Rating
from apps.complaints.models import Complaint, ComplaintType
from apps.trips.models import Trip, TripPassenger
from apps.users.models import User, Role, PendingUser, Vehicle, VehicleType, UserSuspension
from django.utils import timezone
from .utils.validate_password import validar_password_y_confirmacion
from django.contrib.auth import get_user_model
from .utils.validations import validate_phone_number, validate_email, validate_name
from django.utils.translation import gettext_lazy as _
User = get_user_model()
from django.db.models import Avg


class PublicRatingSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer_id.name', read_only=True)
    reviewer_image = serializers.ImageField(source='reviewer_id.profile_image', read_only=True)

    class Meta:
        model = Rating
        fields = ['id', 'stars', 'comment', 'reviewer_name', 'reviewer_image', 'created_at']

class PublicUserProfileSerializer(serializers.ModelSerializer):
    rating_average = serializers.SerializerMethodField()
    recent_comments = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'name', 'profile_image', 'rating_average', 'recent_comments']

    def get_rating_average(self, obj):
        avg = Rating.objects.filter(reviewed_id=obj).aggregate(avg=Avg('stars'))['avg']
        return round(avg, 2) if avg else 0

    def get_recent_comments(self, obj):
        recent = Rating.objects.filter(reviewed_id=obj).order_by('-created_at')[:5]
        return PublicRatingSerializer(recent, many=True).data

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
        """Validar que las contraseñas sean seguras y coincidan."""
        validar_password_y_confirmacion(
            password1=data.get("new_password"),
            password2=data.get("confirm_password"),
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
        """Validar que las contraseñas sean seguras y coincidan."""
        validar_password_y_confirmacion(
            password1=data.get("password"),
            password2=data.get("confirm_password"),
            context_user=None
        )
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
    type = serializers.CharField(source='type_id.name', read_only=True)
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
        """Validar que las contraseñas sean seguras y coincidan."""
        validar_password_y_confirmacion(
            password1=data.get("new_password"),
            password2=data.get("confirm_password"),
            context_user=None
        )
        return data


class ResendNewVerificationCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

# Administar Usuario
# Quejas
class AdminComplaintSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='type_id.name')
    status = serializers.CharField(source='status_id.name')
    reporter = serializers.CharField(source='reporter_id.email')
    admin = serializers.CharField(source='admin_id.email', allow_null=True)
    reported_user = serializers.SerializerMethodField()
    class Meta:
        model = Complaint
        fields = [
            'id',
            'type',
            'status',
            'description',
            'created_at',
            'resolved_at',
            'reporter',
            'admin',
            'reported_user',
        ]
    def get_reported_user(self, obj):
        if obj.reported_user_id:
            return obj.reported_user_id.email
        return None
# Viajes
class AdminTripHistorySerializer(serializers.Serializer):
    trip_id = serializers.IntegerField()
    role = serializers.CharField()  # 'driver' | 'passenger'
    status = serializers.CharField()
    departure_place = serializers.CharField()
    destination = serializers.CharField()
    departure_datetime = serializers.DateTimeField()
class AdminRatingSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.SerializerMethodField()

    class Meta:
        model = Rating
        fields = [
            'id',
            'trip_id',
            'stars',
            'comment',
            'reviewer_name',
            'created_at',
        ]

    def get_reviewer_name(self, obj):
        return f"{obj.reviewer_id.name}"


class AdminUserDetailSerializer(serializers.ModelSerializer):
    vehicles = VehicleSerializer(many=True, read_only=True)

    complaints = serializers.SerializerMethodField()
    trip_history = serializers.SerializerMethodField()
    ratings = serializers.SerializerMethodField()
    rating_average = serializers.SerializerMethodField()
    suspension_info = serializers.SerializerMethodField()
    is_suspended = serializers.SerializerMethodField()
    complaints_made = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = [
            'id',
            'name',
            'phone',
            'created_at',
            'email',
            'is_active',
            'profile_image',
            'is_suspended',
            'suspension_info',  
            'vehicles',
            'complaints',
            'complaints_made',
            'trip_history',
            'rating_average',
            'ratings',
        ]

    def get_complaints(self, user):
        base_qs = Complaint.objects.filter(
            reported_user_id=user
        ).select_related(
            'type_id', 'status_id', 'reporter_id', 'admin_id'
        )

        pending = base_qs.filter(status_id__id=1)
        resolved = base_qs.filter(status_id__id__in=[2, 3])

        return {
            "pending_count": pending.count(),
            "resolved_count": resolved.count(),
            "pending": AdminComplaintSerializer(pending, many=True).data,
            "resolved": AdminComplaintSerializer(resolved, many=True).data,
        }
    def get_complaints_made(self, user):
        qs = Complaint.objects.filter(
            reporter_id=user
        ).select_related(
            'type_id',
            'status_id',
            'reported_user_id',
            'admin_id'
        ).order_by('-created_at')

        result = {}

        for complaint_type in ComplaintType.objects.all():
            type_qs = qs.filter(type_id=complaint_type)

            pending = type_qs.filter(status_id__id=1)
            resolved = type_qs.filter(status_id__id__in=[2, 3])

            result[complaint_type.name.lower()] = {
                "total": type_qs.count(),
                "pending_count": pending.count(),
                "resolved_count": resolved.count(),
                "pending": AdminComplaintSerializer(pending, many=True).data,
                "resolved": AdminComplaintSerializer(resolved, many=True).data,
            }

        return result


    def get_trip_history(self, user):
        history = []

        # 🔹 Como conductor
        driver_trips = Trip.objects.filter(
            driver_id=user
        ).select_related(
            'status_id', 'publication_id'
        )

        for trip in driver_trips:
            history.append({
                "trip_id": trip.id,
                "role": "Conductor",
                "status": trip.status_id.name,
                "departure_place": trip.publication_id.departure_place,
                "destination": trip.publication_id.destination,
                "departure_datetime": trip.publication_id.departure_datetime,
            })

        # 🔹 Como pasajero
        passenger_trips = TripPassenger.objects.filter(
            passenger_id=user
        ).select_related(
            'trip_id__status_id',
            'trip_id__publication_id'
        )

        for tp in passenger_trips:
            history.append({
                "trip_id": tp.trip_id.id,
                "role": "Pasajero",
                "status": tp.status_id.name,
                "departure_place": tp.trip_id.publication_id.departure_place,
                "destination": tp.trip_id.publication_id.destination,
                "departure_datetime": tp.trip_id.publication_id.departure_datetime,
            })

        return history
    def get_ratings(self, user):
        ratings = Rating.objects.filter(
            reviewed_id=user
        ).select_related(
            'reviewer_id',
            'trip_id'
        ).order_by('-created_at')

        return AdminRatingSerializer(ratings, many=True).data

    def get_rating_average(self, user):
        avg = Rating.objects.filter(
            reviewed_id=user
        ).aggregate(avg=Avg('stars'))['avg']

        return round(avg, 2) if avg else None

    def get_suspension_info(self, user):
        return check_and_handle_suspension(user)
    def get_is_suspended(self, user):
        suspension = check_and_handle_suspension(user)
        return suspension is not None


def check_and_handle_suspension(user):
    now = timezone.now()

    suspension = UserSuspension.objects.filter(
        user_id=user
    ).order_by('-start_date').first()

    if not suspension:
        return None

    # permanente
    if suspension.is_permanent:
        return {
            "is_permanent": True,
            "remaining_days": None,
            "reason": suspension.reason,
        }

    # temporal activa
    if suspension.end_date and suspension.end_date > now:
        remaining_days = (suspension.end_date.date() - now.date()).days

        return {
            "is_permanent": False,
            "remaining_days": max(remaining_days, 0),
            "reason": suspension.reason,
        }

    # 🔹 si llegó aquí significa que ya expiró
    if user.is_suspended:
        user.is_suspended = False
        user.save(update_fields=["is_suspended"])

    return None