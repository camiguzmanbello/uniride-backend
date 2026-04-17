from rest_framework import serializers
# users/serializers/report_serializers.py
from rest_framework import serializers
from apps.users.models import User, UserSuspension, AuditLog, Vehicle
from apps.trips.models import Trip, TripPassenger
from apps.ratings.models import Rating

class ChartSerializer(serializers.Serializer):
    labels = serializers.ListField(
        child=serializers.CharField()
    )
    values = serializers.ListField(
        child=serializers.IntegerField()
    )


class ChartsSerializer(serializers.Serializer):
    trips_per_day = ChartSerializer()
    trip_status = ChartSerializer()
    users_status = ChartSerializer()
class AdminDashboardSerializer(serializers.Serializer):
    active_users = serializers.IntegerField()
    active_trips = serializers.IntegerField()
    pending_complaints = serializers.IntegerField()

    
    charts = ChartsSerializer()

# Reportes
# -------------------
# Usuario
# -------------------
class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email"]
class AdminConfirmationSerializer(serializers.ModelSerializer):
    actor = SimpleUserSerializer()
    target_user = SimpleUserSerializer()

    class Meta:
        model = AuditLog
        fields = [
            "actor",
            "target_user",
            "reason",
            "timestamp"
        ]
class VehiclePreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ["plate", "brand", "model", "color"]

class UserReportSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="role_id.name")
    vehicles = VehiclePreviewSerializer(many=True)

    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "phone",
            "role",
            "created_at",
            "vehicles",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Admin → NO vehículos
        if data["role"] == "Administrador":
            data["vehicles"] = []

        return data



# -------------------
# Viajes
# -------------------
class TripPassengerReportSerializer(serializers.ModelSerializer):
    passenger_name = serializers.CharField(source="passenger_id.name")
    passenger_email = serializers.EmailField(source="passenger_id.email")
    status = serializers.CharField(source="status_id.name")

    class Meta:
        model = TripPassenger
        fields = (
            "passenger_name",
            "passenger_email",
            "seats_reserved",
            "status",
            "joined_at",
        )
class TripReportSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source="driver_id.name")
    driver_email = serializers.EmailField(source="driver_id.email")
    status = serializers.CharField(source="status_id.name")

    departure_place = serializers.CharField(
        source="publication_id.departure_place"
    )
    destination = serializers.CharField(
        source="publication_id.destination"
    )
    departure_datetime = serializers.DateTimeField(
        source="publication_id.departure_datetime"
    )
    available_seats = serializers.IntegerField(
        source="publication_id.available_seats"
    )

    passengers = TripPassengerReportSerializer(many=True)

    class Meta:
        model = Trip
        fields = (
            "id",
            "driver_name",
            "driver_email",
            "status",
            "departure_place",
            "destination",
            "departure_datetime",
            "available_seats",
            "created_at",
            "finalized_at",
            "passengers",
        )


# -------------------
# Calificaciones
# -------------------
class RatingSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source="reviewer_id.name", read_only=True)
    reviewed_name = serializers.CharField(source="reviewed_id.name", read_only=True)
    trip_id = serializers.IntegerField(source="trip_id.id", read_only=True)

    class Meta:
        model = Rating
        fields = ["trip_id", "reviewer_name", "reviewed_name", "stars", "comment", "created_at"]
# -------------------
# Suspensiones
# -------------------
class UserSuspensionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user_id.name", read_only=True)
    admin_name = serializers.CharField(source="admin_id.name", read_only=True)

    class Meta:
        model = UserSuspension
        fields = ["user_name", "admin_name", "reason", "start_date", "end_date", "is_permanent", "created_at"]
# -------------------
# Auditoría
# -------------------
class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.name", read_only=True)
    target_name = serializers.CharField(source="target_user.name", read_only=True)

    class Meta:
        model = AuditLog
        fields = ["actor_name", "action", "target_name", "reason", "extra_data", "timestamp"]


# -------------------
# Emparejamientos
# -------------------
