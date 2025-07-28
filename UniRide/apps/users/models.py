from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.name

class User(AbstractUser):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=13, unique=True, null=True, blank=True)
    profile_image = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    role_id = models.ForeignKey(Role, on_delete=models.PROTECT, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)

     # Desactivar campos que no se necesitan de AbstractUser
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=150, null=True, blank=True)
    last_name = models.CharField(max_length=150, null=True, blank=True)
    is_superuser=models.BooleanField(null=True, blank=True)
    date_joined=models.DateTimeField(null=True, blank=True) 
    is_verified=models.BooleanField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phone']

    class Meta:
        indexes = [
            models.Index(fields=['email']),
        ]
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.name} ({self.email})"
    
class PendingUser(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=False)
    phone = models.CharField(max_length=13)
    password = models.CharField(max_length=128)  # Guardar el hash
    role_id = models.ForeignKey('Role', on_delete=models.PROTECT, null=True)
    profile_image = models.TextField(null=True, blank=True)
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)
    registrado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios_preregistrados",
        help_text="Administrador que hizo el preregistro"
    )
    def __str__(self):
        return f"{self.email} - {self.code}"

class VehicleType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = 'Tipo de Vehículo'
        verbose_name_plural = 'Tipos de Vehículo'

    def __str__(self):
        return self.name


class Vehicle(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    type_id = models.ForeignKey(VehicleType, on_delete=models.PROTECT)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    plate = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['plate']),
        ]
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'

    def __str__(self):
        return f"{self.brand} - {self.plate}"


class UserSuspension(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='suspensions')
    admin_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applied_suspensions')
    reason = models.TextField()
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    is_permanent = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Suspensión de Usuario'
        verbose_name_plural = 'Suspensiones de Usuario'

    def __str__(self):
        return f"Suspensión a {self.user_id.name}"


class AuditLog(models.Model):
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text="Usuario que realizó la acción"
    )
    action = models.CharField(max_length=100, help_text="Nombre del evento auditado, ej: LOGIN_EXITOSO")
    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_targets',
        help_text="Usuario sobre el que se actuó, si aplica"
    )
    reason = models.TextField(null=True, blank=True, help_text="Motivo de la acción (si aplica)")
    extra_data = models.JSONField(null=True, blank=True, help_text="Datos adicionales relevantes")
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'
        ordering = ['-timestamp']


    def __str__(self):
        actor_email = self.actor.email if self.actor else "Usuario eliminado"
        return f"{actor_email} → {self.action} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"

