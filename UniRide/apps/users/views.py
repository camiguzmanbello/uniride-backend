from django.contrib.auth import authenticate
from django.utils.timezone import now
# Crear vistas basadas en clases (APIView)
from rest_framework.views import APIView
from rest_framework.response import Response  # Retornar respuestas (Response)
# Definir quién puede acceder a cada vista (permissions)
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status, permissions, viewsets
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import get_user_model
import logging
from apps.users.serializer import *
from apps.users.models import User, Role, PendingUser
from apps.users.permissions import IsSelfOrAdmin
from rest_framework.generics import RetrieveUpdateDestroyAPIView, RetrieveUpdateAPIView
from django.core.mail import send_mail
import random
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from apps.core.token_generation import generate_reset_token, verify_reset_token
from rest_framework.exceptions import ValidationError
User = get_user_model()
logger = logging.getLogger(__name__)
from .utils.jwt_cookies import generar_respuesta_con_tokens, set_tokens_en_response
from .utils.audit import registrar_log
from .authentication import CookieJWTAuthentication  # o desde donde la hayas definido

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data["email"].lower()
            password = serializer.validated_data["password"]

            user = authenticate(request, email=email, password=password)

            if user is not None:
                user.last_login = now()
                user.save(update_fields=["last_login"])


                registrar_log(
                    actor=user,
                    action="LOGIN_EXITOSO",
                    extra_data={
                        "ip": request.META.get("REMOTE_ADDR"),
                        "user_agent": request.META.get("HTTP_USER_AGENT")
                    }

                )

                return generar_respuesta_con_tokens(user, message="Login exitoso")

            registrar_log(
                actor=None,
                action="LOGIN_FALLIDO",
                extra_data={
                    "ip": request.META.get("REMOTE_ADDR"),
                    "user_agent": request.META.get("HTTP_USER_AGENT"),
                    "error": "Credenciales inválidas",
                    "email": email
                }
            )

            return Response({"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error interno durante el login: {str(e)}")
            return Response(
                {"error": "Error interno del servidor. Inténtalo más tarde."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserMeView(APIView):
    authentication_classes = [CookieJWTAuthentication] 
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)
    
#Hace que el usuario no tenga que hacer el proceso de login ya que lo hace automaticamente 
class RefreshTokenView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response({"error": "Refresh token no encontrado"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            if settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS", False):
                user_id = refresh["user_id"]
                user = User.objects.get(id=user_id)
                new_refresh = str(RefreshToken.for_user(user))
            else:
                new_refresh = str(refresh)

            response = Response({
                "message": "Token renovado con éxito"
            })

            return set_tokens_en_response(response, access_token, new_refresh)

        except TokenError:
            return Response({"error": "Token inválido o expirado"}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)


class PerfilView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        user = request.user
        return Response({
            "email": user.email,
            "name": user.name,
            "phone": user.phone
        })
        
    @swagger_auto_schema(request_body=EditarPerfilSerializer)
    def patch(self, request):
        user = request.user
        old_data = {"name": user.name, "phone": user.phone}

        serializer = EditarPerfilSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            cambios = {
                campo: serializer.validated_data[campo]
                for campo in serializer.validated_data
                if serializer.validated_data[campo] != old_data.get(campo)
            }

            if cambios:
                registrar_log(
                    actor=user,
                    action="ACTUALIZAR_PERFIL",
                    target_user=user,
                    extra_data={"cambios": cambios}
                )

            return Response({"message": "Perfil actualizado correctamente"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = request.user
        user.is_active = False
        user.phone = None
        user.role_id_id= None  
        user.is_staff = False 
        user.set_unusable_password()
        user.save()

        registrar_log(
            actor=user,
            action="SOFT_DELETE_ADMIN",
            target_user=user,
            reason="Desactivación voluntaria de administrador"
        )
        response = Response({"message": "Administrador desactivado correctamente."}, status=status.HTTP_200_OK)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token") 
        return response


class PreRegisterAdminView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def _generate_code(self):
        while True:
            code = str(random.randint(100000, 999999))
            if not PendingUser.objects.filter(code=code, expires_at__gt=timezone.now()).exists():
                return code

    def _normalize_phone_number(self, phone: str) -> str:
        return ''.join(filter(str.isdigit, phone))

    @swagger_auto_schema(request_body=PendingAdminUserSerializer)
    def post(self, request):
        serializer = PendingAdminUserSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=400)

        email = serializer.validated_data["email"]
        phone = self._normalize_phone_number(serializer.validated_data["phone"])
        name = serializer.validated_data["name"]

        code = self._generate_code()
        expires = timezone.now() + timedelta(minutes=10)

        # ===== VALIDAR EN USUARIOS ACTIVOS =====
        user_qs = User.objects.filter(email__iexact=email)
        if user_qs.exists():
            user = user_qs.first()
            if user.is_active:
                return Response({'error': 'Este correo ya está registrado.'}, status=400)
            elif User.objects.filter(phone=phone).exclude(id=user.id).exists():
                return Response({'error': 'Este número ya está en uso por otro usuario.'}, status=400)

        elif User.objects.filter(phone=phone).exists():
            return Response({'error': 'Este número ya está en uso por otro usuario.'}, status=400)

        # ===== VALIDAR EN PENDING USER =====
        existing_pending = PendingUser.objects.filter(email__iexact=email).first()
        other_pending = PendingUser.objects.filter(phone=phone).exclude(email__iexact=email).first()
        if other_pending:
            return Response({'error': 'Este número ya está en uso por otro preregistro.'}, status=400)

        # ===== ACTUALIZAR O CREAR PENDING USER =====
        if existing_pending:
            existing_pending.name = name
            existing_pending.phone = phone
            existing_pending.code = code
            existing_pending.expires_at = expires
            existing_pending.save()
        else:
            PendingUser.objects.create(
                name=name,
                email=email,
                phone=phone,
                code=code,
                expires_at=expires,
                role_id_id=1,  
                registrado_por=request.user 
            )

        # ===== ENVIAR CORREO =====
        confirmation_url = f"https://tuapp.com/confirmar-admin/{code}/"
        send_mail(
            subject='¡Confirma tu registro como Administrador en UniRide!',
            message=(
                f"Hola,\n\n"
                f"¡Bienvenido a UniRide!\n\n"
                f"Has sido registrado como administrador en nuestra plataforma. Para completar tu registro, por favor utiliza el siguiente código de verificación:\n\n"
                f"🔐 Código: {code}\n\n"
                f"Y haz clic en el siguiente enlace para confirmar tu cuenta:\n"
                f"{confirmation_url}\n\n"
                f"Este enlace expirará en 10 minutos.\n\n"
                f"Gracias por formar parte del equipo,\n"
                f"El equipo de UniRide 🚗"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        return Response({'message': 'Correo de confirmación enviado o reenviado.'}, status=200)


class ConfirmAdminView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(request_body=ConfirmAdminSerializer)
    def post(self, request):
        serializer = ConfirmAdminSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        code = serializer.validated_data['code']
        password = serializer.validated_data['password']

        try:
            pending = PendingUser.objects.get(code=code, expires_at__gt=timezone.now())
        except PendingUser.DoesNotExist:
            return Response({"error": "Código inválido o expirado"}, status=400)

        if pending.role_id_id != 1:
            return Response({"error": "No tienes permiso para confirmar esta cuenta."}, status=403)

        # Si ya existe un usuario con ese email y está inactivo → reactivarlo
        try:
            user = User.objects.get(email__iexact=pending.email)
            if not user.is_active:
                user.name = pending.name
                user.phone = pending.phone
                user.set_password(password)
                user.is_active = True
                user.is_staff = True
                user.role_id_id = 1
                user.save()
            else:
                return Response({"error": "Este usuario ya está activo."}, status=400)

        except User.DoesNotExist:
            # Si no existe, crear nuevo usuario
            user = User.objects.create_user(
                name=pending.name,
                username=pending.email,
                email=pending.email,
                phone=pending.phone,
                password=password,
                is_active=True,
                is_staff=True,
                role_id_id=1,
            )
            # ConfirmAdminView - después de activar o crear el usuario

            registrar_log(
                actor=pending.registrado_por,  
                action="ACCION_REGISTRO_ADMIN",
                target_user=user,
                reason='Confirmación de cuenta de administrador desde preregistro',
                extra_data={'email': user.email, 'phone': user.phone},
            )
        # Eliminar el registro pendiente
        pending.delete()

        return Response({"message": "Cuenta de administrador confirmada con éxito."})

#Borra ambas cookies 
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            response = Response({"message": "Logout exitoso"},
                                status=status.HTTP_200_OK)
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")
            return response
        except Exception as e:
            logger.error(f"Error durante logout: {str(e)}")
            return Response(
                {"error": "Ocurrió un error durante el logout. Inténtalo más tarde."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RoleView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        roles = Role.objects.all()
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=RoleSerializer)
    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        if serializer.is_valid():
            role = serializer.save()
            return Response({
                "message": "Rol creado exitosamente",
                "role": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserView(APIView):
    # debe ser solo para admins
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(request_body=UserSerializer)
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(is_verified=False)

            return Response({
                "message": "Usuario creado exitosamente.",
                "user": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RegisterView(APIView):

    permission_classes = [permissions.AllowAny]

    def _validate_user_existence(self, request, email, phone):
        """Valida que el email y phone no existan en User ni PendingUser."""
        status_err = status.HTTP_409_CONFLICT
        status_ok = status.HTTP_200_OK

        if User.objects.filter(email__iexact=email).exists():
            return "Este correo ya está registrado."
        if User.objects.filter(phone=phone).exists():
            return "Este número de teléfono ya está registrado."
        if PendingUser.objects.filter(email__iexact=email).exists():
            return "Ya hay un proceso de verificación en curso para este correo."
        if PendingUser.objects.filter(phone=phone).exists():
            return Response({"error": "Ya hay un proceso de verificación en curso para este número."}, status=status_err)
        #Si el usuario existe y está inactivo, lo reactivamos
        existing_user = User.objects.filter(email=email).first()
        if existing_user and not existing_user.is_active:
            existing_user.is_active = True
            existing_user.phone = phone  # Actualiza si es necesario
            existing_user.password = make_password(request.data.get('password'))  # Actualiza contraseña
            existing_user.save()
            #esto reactivara los vehiculos del usuario
            existing_user.vehicles.filter(is_active=False).update(is_active=True)

            return Response({"message": "Cuenta reactivada exitosamente."}, status=status_ok)

    def _generate_verification_code(self):
        """Genera un código único de 6 dígitos no expirado."""
        while True:
            code = str(random.randint(100000, 999999))
            if not PendingUser.objects.filter(code=code, expires_at__gt=timezone.now()).exists():
                return code

    @swagger_auto_schema(request_body=PendingUserSerializer)
    def post(self, request):
        serializer = PendingUserSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            phone = serializer.validated_data['phone']

            # Validación personalizada
            validate = self._validate_user_existence(email, phone)
            if validate:
                return validate

            # Generar código y tiempo de expiración
            code = self._generate_verification_code()
            expiration = timezone.now() + timedelta(minutes=10)
            hashed_password = make_password(
                serializer.validated_data['password'])

            # Crear usuario temporal
            pending = PendingUser.objects.create(
                name=serializer.validated_data['name'],
                email=email,
                phone=phone,
                password=hashed_password,
                role_id=Role.objects.filter(name='Usuario').first() or None,
                profile_image=serializer.validated_data.get('profile_image'),
                code=code,
                expires_at=expiration
            )

            # Enviar correo
            send_mail(
                subject='Código de verificación de UniRide',
                message=(
                    f'Hola,\n\n'
                    f'Estás a punto de registrarte en UniRide.\n'
                    f'Tu código de verificación es: {code}\n\n'
                    f'Este código expirará en 10 minutos.\n\n'
                    f'Si no solicitaste este registro, ignora este mensaje.\n\n'
                    f'Gracias,\nEl equipo de UniRide.'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            return Response(
                {"message": "Código enviado. Verifica tu correo.", "email": email},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSelfProfileView(RetrieveUpdateAPIView):
    
    permission_classes = [IsAuthenticated]

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
    
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = False
        user.save()
        # Soft delete de todos los vehículos del usuario
        user.vehicles.filter(is_active=True).update(is_active=False)
        return Response(
            {"message": "Usuario desactivado exitosamente junto con sus vehiculos."},
            status=status.HTTP_204_NO_CONTENT
        )


class UserVehicleProfileView(RetrieveUpdateAPIView):
    
    permission_classes = [IsAuthenticated]

    serializer_class = VehicleSerializer

    def get(self, request, *args, **kwargs):
        user_vehicles_queryset = request.user.vehicles.filter(is_active=True) # Obtiene el QuerySet
        if not user_vehicles_queryset:
            return Response({"message": "No tienes vehículos activos."}, status=status.HTTP_404_NOT_FOUND)
        serializer = VehicleSerializer(user_vehicles_queryset, many=True)
        return Response(serializer.data)
    
    
class DeactivateSingleVehicleView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, vehicle_id):
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id, user_id=request.user)
        except Vehicle.DoesNotExist:
            return Response({"error": "Vehículo no encontrado o no pertenece al usuario."},
                            status=status.HTTP_404_NOT_FOUND)

        vehicle.is_active = False
        vehicle.save()
        return Response({"message": "Vehículo desactivado exitosamente."}, status=status.HTTP_204_NO_CONTENT)
    

class DeactivateAllVehiclesView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        vehicles = request.user.vehicles.filter(is_active=True)
        count = vehicles.update(is_active=False)
        return Response(
            {"message": f"{count} vehículo(s) desactivado(s) exitosamente."},
            status=status.HTTP_204_NO_CONTENT
        )


class VehicleTypeView(viewsets.ModelViewSet):

    permission_classes = [permissions.IsAuthenticated] #debe ser solo para admins

    queryset = VehicleType.objects.all()
    serializer_class = VehicleTypeSerializer


class VehicleView(viewsets.ModelViewSet):
    serializer_class = VehicleSerializer
    queryset = Vehicle.objects.all()

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [permissions.IsAdminUser()]

    def create(self, request, *args, **kwargs):
        plate = request.data.get("plate")

        if not plate:
            return Response({"error": "La placa es obligatoria."}, status=status.HTTP_400_BAD_REQUEST)

        # Intentar encontrar vehículo existente con esa placa
        existing_vehicle = Vehicle.objects.filter(plate=plate).first()

        if existing_vehicle:
            if existing_vehicle.user_id != request.user:
                return Response(
                    {"error": "Esta placa ya está registrada por otro usuario."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif not existing_vehicle.is_active:
                # Reactivar vehículo
                existing_vehicle.is_active = True
                existing_vehicle.save()
                return Response(
                    {"message": "Vehículo reactivado exitosamente."},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": "Ya tienes un vehículo registrado con esta placa."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Si no existe, se crea normalmente
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user_id=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserPendingEditDeleteView(RetrieveUpdateDestroyAPIView):
    queryset = PendingUser.objects.all()
    serializer_class = PendingUserSerializer

    permission_classes = [permissions.AllowAny] #admins

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "Usuario pendiente encontrado exitosamente",
            "pending_user": serializer.data
        }, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response({
            "message": "Usuario pendiente actualizado exitosamente",
            "pending_user": response.data
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        return Response({
            "message": "Usuario pendiente actualizado parcialmente",
            "pending_user": response.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({
            "message": "Usuario pendiente eliminado exitosamente"
        }, status=status.HTTP_204_NO_CONTENT)


class UserPendingView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        pending_users = PendingUser.objects.all()
        serializer = PendingUserSerializer(pending_users, many=True)
        return Response({
            "message": "Usuarios pendientes encontrados exitosamente",
            "pending_users": serializer.data
        }, status=status.HTTP_200_OK)


class VerifyPendingUserView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(request_body=VerifyCodeSerializer)
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data['code']

            # Supón que el frontend envió el código pero ya conoce el email (guardado localmente)
            # Por ahora, recuperamos el único PendingUser con ese código válido
            pending = PendingUser.objects.filter(
                code=code, expires_at__gt=timezone.now()).first()

            if pending:
                user = User.objects.create(
                    name=pending.name,
                    email=pending.email,
                    phone=pending.phone,
                    password=pending.password,  # Ya hasheada
                    role_id=pending.role_id,
                    profile_image=pending.profile_image,
                    is_verified=True
                )
                pending.delete()
                return Response({"message": "Usuario creado y verificado exitosamente."}, status=status.HTTP_201_CREATED)

            return Response({"error": "Código inválido o expirado."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserEditDeleteView(RetrieveUpdateDestroyAPIView):

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            return [IsSelfOrAdmin()]
        elif self.request.method == 'DELETE':
            return [permissions.IsAdminUser()]
        return [IsSelfOrAdmin()]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "Usuario encontrado exitosamente",
            "user": serializer.data
        }, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response({
            "message": "Usuario actualizado exitosamente",
            "user": response.data
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        return Response({
            "message": "Usuario actualizado parcialmente",
            "user": response.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response({
            "message": "Usuario eliminado exitosamente"
        }, status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(request_body=PasswordResetRequestSerializer)
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "El correo es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "No existe un usuario con ese correo."}, status=status.HTTP_404_NOT_FOUND)

        token = generate_reset_token(email)
        reset_link = f"http://localhost:3000/reset-password?token={token}"

        send_mail(
            subject='Recuperación de contraseña - UniRide',
            message=(
                f"Hola,\n\n"
                f"Haz clic en el siguiente enlace para restablecer tu contraseña:\n"
                f"{reset_link}\n\n"
                f"Este enlace expirará en 10 minutos.\n\n"
                f"Si no solicitaste este cambio, puedes ignorar este mensaje."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )

        return Response({"message": "Enlace de recuperación enviado al correo."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(request_body=PasswordResetConfirmSerializer)
    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not all([token, new_password]):
            return Response({"error": "Token y nueva contraseña requeridos."}, status=status.HTTP_400_BAD_REQUEST)

        email = verify_reset_token(token)
        if not email:
            return Response({"error": "Token inválido o expirado."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        user.password = make_password(new_password)
        user.save()

        return Response({"message": "Contraseña actualizada correctamente."}, status=status.HTTP_200_OK)

class CambiarPasswordView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(request_body=CambiarPasswordSerializer)
    def post(self, request):
        serializer = CambiarPasswordSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = request.user

            if not user.check_password(serializer.validated_data['old_password']):
                return Response({"old_password": ["La contraseña actual es incorrecta."]}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return generar_respuesta_con_tokens(user, message="Contraseña actualizada y sesión renovada.")

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)