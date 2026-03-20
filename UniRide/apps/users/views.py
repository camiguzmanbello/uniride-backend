import cloudinary
from .authentication import CookieJWTAuthentication
from .utils.audit import registrar_log
from .utils.jwt_cookies import generar_respuesta_con_tokens, set_tokens_en_response
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
from apps.users.models import User, Role, PendingUser, UserSuspension, AuditLog
from apps.users.permissions import IsSelfOrAdmin
from rest_framework.generics import RetrieveUpdateDestroyAPIView, RetrieveUpdateAPIView
import random
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from apps.core.token_generation import generate_reset_token, verify_reset_token
from rest_framework.exceptions import ValidationError
from apps.users.utils.utils import generate_verification_code, send_code_email, send_suspension_email
from rest_framework.parsers import MultiPartParser, FormParser # Para manejar archivos en requests
from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.complaints.models import Complaint
from apps.users.utils.suspension_service import check_and_handle_suspension
from .utils.cloudinary_utils import delete_cloudinary_image, extract_public_id_from_url


User = get_user_model()
logger = logging.getLogger(__name__)


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
                # 🔍 Chequear suspensión
                suspension_info = check_and_handle_suspension(user)
                if suspension_info:
                    if suspension_info["is_permanent"]:
                        message = "Tu cuenta está suspendida de forma permanente."
                    else:
                        days = suspension_info["remaining_days"]
                        message = f"Tu cuenta está suspendida por {days} día(s)." if days is not None else \
                                "Tu cuenta está suspendida temporalmente."
                    registrar_log(
                        actor=user,
                        action="LOGIN_BLOQUEADO_SUSPENSION",
                        extra_data={
                            "reason": suspension_info["reason"],
                            "remaining_days": suspension_info["remaining_days"]
                        }
                    )

                    return Response(
                        {
                            "error": message,
                            "reason": suspension_info["reason"],
                            "remaining_days": suspension_info["remaining_days"]
                        },
                        status=status.HTTP_403_FORBIDDEN
                    )

                # Login normal
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

# Hace que el usuario no tenga que hacer el proceso de login ya que lo hace automaticamente
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

        serializer = EditarPerfilSerializer(
            user, data=request.data, partial=True)
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

        try:
            user = request.user
            user.is_active = False
            user.phone = None
            user.role_id_id = None  
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

        except Exception as e:
            return Response(
                {"error": "No se pudo desactivar el administrador. Intente en otro momento."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from email.mime.image import MIMEImage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from pathlib import Path
import os
import random
from datetime import timedelta
from django.utils import timezone

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

        # ========================
        # SERIALIZER
        # ========================
        serializer = PendingAdminUserSerializer(
            data=request.data, context={'request': request}
        )
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=400)

        email = serializer.validated_data["email"].lower()
        phone = self._normalize_phone_number(serializer.validated_data["phone"])
        name = serializer.validated_data["name"]

        code = self._generate_code()
        expires = timezone.now() + timedelta(minutes=10)

        # ========================
        # VALIDACIONES USER
        # ========================
        user_qs = User.objects.filter(email__iexact=email)
        if user_qs.exists():
            user = user_qs.first()
            if user.is_active:
                return Response({'error': 'Este correo ya está registrado.'}, status=400)
            elif User.objects.filter(phone=phone).exclude(id=user.id).exists():
                return Response({'error': 'Este número ya está en uso por otro usuario.'}, status=400)

        elif User.objects.filter(phone=phone).exists():
            return Response({'error': 'Este número ya está en uso por otro usuario.'}, status=400)

        # ========================
        # VALIDACIONES PENDING
        # ========================
        existing_pending = PendingUser.objects.filter(email__iexact=email).first()
        other_pending = PendingUser.objects.filter(phone=phone).exclude(email__iexact=email).first()

        if other_pending:
            return Response({'error': 'Este número ya está en uso por otro preregistro.'}, status=400)

        # ========================
        # CREAR / ACTUALIZAR PENDING
        # ========================
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

        # ===========================
        # CORREO HTML CON LOGO
        # ===========================

        confirmation_url = f"https://app.unirideweb.online/confirm-admin?code={code}&email={email}"

        logo_path = Path(settings.BASE_DIR) / "email_assets" / "logo-uniride2.png"
        

        # Renderizar HTML
        html_content = render_to_string("preregister.html", {
            "name": name,
            "code": code,
            "confirmation_url": confirmation_url,
        })

        text_content = strip_tags(html_content)

        email_message = EmailMultiAlternatives(
            subject="¡Confirma tu registro como Administrador en UniRide!",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )

        email_message.attach_alternative(html_content, "text/html")

        
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                logo_data = f.read()
            email_image = MIMEImage(logo_data)
            email_image.add_header("Content-ID", "<logo>")
            email_message.attach(email_image)   # ← CORREGIDO
        else:
            print("WARNING: Logo no encontrado:", logo_path)

        # Enviar correo
        email_message.send()

        return Response({"message": "Correo de confirmación enviado o reenviado."}, status=200)


class ConfirmAdminView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(request_body=ConfirmAdminSerializer)
    def post(self, request):
        serializer = ConfirmAdminSerializer(
            data=request.data, context={'request': request}
        )
        if not serializer.is_valid():
            # Unificar errores para frontend
            formatted_errors = {}
            for key, value in serializer.errors.items():
                formatted_errors[key] = value
            return Response(formatted_errors, status=400)

        code = serializer.validated_data['code']
        password = serializer.validated_data['password']
        confirm_password = serializer.validated_data.get('confirm_password')

        # ================================
        # VALIDACIÓN DE CONTRASEÑA
        # ================================
        if password != confirm_password:
            return Response(
                {"confirm_password": ["Las contraseñas no coinciden."]},
                status=400
            )

        # ================================
        # VALIDACIONES DEL CÓDIGO
        # ================================
        if not code.isdigit():
            return Response(
                {"code": ["El código debe contener solo números."]},
                status=400
            )

        if len(code) != 6:
            return Response(
                {"code": ["El código debe tener exactamente 6 dígitos."]},
                status=400
            )

        # ================================
        # BUSCAR EL PENDING USER
        # ================================
        try:
            pending = PendingUser.objects.get(
                code=code, expires_at__gt=timezone.now()
            )
        except PendingUser.DoesNotExist:
            return Response(
                {"code": ["Código inválido o expirado."]},
                status=400
            )

        # ================================
        # VALIDAR QUE SEA ADMIN
        # ================================
        if pending.role_id_id != 1:
            return Response(
                {"detail": "No tienes permiso para confirmar esta cuenta."},
                status=403
            )

        # ================================
        # ACTIVAR O CREAR USUARIO
        # ================================
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
                return Response(
                    {"detail": "Este usuario ya está activo."},
                    status=400
                )
        except User.DoesNotExist:
            # Crear nuevo usuario
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

            # Registrar auditoría
            registrar_log(
                actor=pending.registrado_por,
                action="ACCION_REGISTRO_ADMIN",
                target_user=user,
                reason="Confirmación de cuenta de administrador desde preregistro",
                extra_data={'email': user.email, 'phone': user.phone},
            )

        # ================================
        # ELIMINAR PREREGISTRO
        # ================================
        pending.delete()

        return Response(
            {"message": "Cuenta de administrador confirmada con éxito."},
            status=200
        )

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            response = Response(
                {"message": "Logout exitoso"},
                status=status.HTTP_200_OK
            )

            response.set_cookie(
                key="access_token",
                value="",
                httponly=True,
                secure=True,
                samesite="None",
                domain=".unirideweb.online",
                max_age=0
            )

            response.set_cookie(
                key="refresh_token",
                value="",
                httponly=True,
                secure=True,
                samesite="None",
                domain=".unirideweb.online",
                max_age=0
            )

            return response

        except Exception as e:
            logger.error(f"Error durante logout: {str(e)}")
            return Response(
                {"error": "Ocurrió un error durante el logout."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RoleView(APIView):
    permission_classes = [permissions.AllowAny]

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


class UserView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserSerializer



class RegisterView(APIView):

    permission_classes = [permissions.AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def _validate_user_existence(self, request, email, phone):
        status_err = status.HTTP_409_CONFLICT
        status_ok = status.HTTP_200_OK

        existing_user = User.objects.filter(email__iexact=email).first()

        # Si el usuario existe y está inactivo, intentamos reactivarlo
        if existing_user and not existing_user.is_active:
            # Validar que el número de teléfono no esté siendo usado por otro usuario activo
            if User.objects.filter(phone=phone).exclude(id=existing_user.id).exists():
                return Response({"error": "Este número de teléfono ya está registrado por otro usuario."}, status=status_err)

            return None

        # Si el usuario existe y está activo
        if existing_user and existing_user.is_active:
            return Response({"error": "Este correo ya está registrado."}, status=status_err)

        # Validaciones para nuevos registros
        if User.objects.filter(phone=phone).exists():
            return Response({"error": "Este número de teléfono ya está registrado."}, status=status_err)

        if PendingUser.objects.filter(email__iexact=email).exists():
            return Response({"error": "Ya hay un proceso de verificación en curso para este correo."}, status=status_err)
        if PendingUser.objects.filter(phone=phone).exists():
            return Response({"error": "Ya hay un proceso de verificación en curso para este número."}, status=status_err)

        return None

    @swagger_auto_schema(request_body=PendingUserSerializer)
    def post(self, request):
        serializer = PendingUserSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            phone = serializer.validated_data['phone']

            # Validación personalizada
            validate = self._validate_user_existence(request, email, phone)
            if validate:
                return validate

            # Generar código y tiempo de expiración
            code = generate_verification_code()
            expiration = timezone.now() + timedelta(minutes=10)
            hashed_password = make_password(
                serializer.validated_data['password'])

            # Crear usuario temporal
            # Obtener el rol 'Usuario' por defecto, lanzando excepción clara si no existe
            try:
                default_role = Role.objects.get(name='Usuario')
            except Role.DoesNotExist:
                logger.error("Rol 'Usuario' no encontrado en la base de datos")
                return Response(
                    {"error": "Error de configuración: rol de usuario no disponible"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            pending = PendingUser.objects.create(
                name=serializer.validated_data['name'],
                email=email,
                phone=phone,
                password=hashed_password,
                role_id=default_role,
                profile_image=request.FILES.get('profile_image'),
                code=code,
                expires_at=expiration
            )

            # Enviar correo
            send_code_email(
                subject="Verificación de Cuenta - UniRide",
                message=(
                    f'Hola {pending.name},<br><br>'
                    f'Estás a punto de registrarte en UniRide, '
                    f'tu código de verificación es:<br>'
                ),
                finalmessage=(
                    f'Este código expirará en 10 minutos.<br><br>'
                    f'Si no solicitaste este registro, ignora este mensaje.<br><br>'
                    f'Gracias, el equipo de UniRide.'
                ),
                email=email,
                code=code
            )

            return Response(
                {"message": "Se te ha enviado un codigo de verificación, Verifica tu correo.", "email": email},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublicUserProfileView(APIView):
    """
    Vista para obtener el perfil público de cualquier usuario.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(responses={200: PublicUserProfileSerializer()})
    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id, is_active=True)
        serializer = PublicUserProfileSerializer(user)
        return Response(serializer.data)

class UserSelfProfileView(RetrieveUpdateAPIView):

    permission_classes = [IsAuthenticated]

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        old_image_url = None
        
        # Obtener URL completa de la imagen anterior
        if user.profile_image:
            old_image_url = user.profile_image.url
        
        # Realizar la actualización
        response = super().update(request, *args, **kwargs)
        
        # Obtener usuario actualizado
        updated_user = self.get_object()
        new_image_url = updated_user.profile_image.url if updated_user.profile_image else None
        
        # Verificar si realmente cambió la imagen
        if old_image_url and new_image_url:
            # Extraer public_ids para comparación robusta
            old_public_id = extract_public_id_from_url(old_image_url)
            new_public_id = extract_public_id_from_url(new_image_url)
            
            # Solo borrar si son imágenes completamente diferentes
            if old_public_id and new_public_id and old_public_id != new_public_id:
                delete_cloudinary_image(old_image_url)
        elif old_image_url and not new_image_url:
            # Caso: Se eliminó la imagen (se estableció a None)
            delete_cloudinary_image(old_image_url)
        
        return response


    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = False

        if user.profile_image:
            delete_cloudinary_image(str(user.profile_image))
            user.profile_image = None

        user.save()
        # Soft delete de relaciones
        user.vehicles.filter(is_active=True).update(is_active=False)
        user.publications.filter(is_active=True).update(is_active=False)
        return Response(
            {"message": "Usuario desactivado exitosamente junto con sus demas relaciones."},
            status=status.HTTP_204_NO_CONTENT
        )


class UserVehicleProfileView(RetrieveUpdateAPIView):

    permission_classes = [IsAuthenticated]

    serializer_class = VehicleSerializer

    def get(self, request, *args, **kwargs):
        user_vehicles_queryset = request.user.vehicles.filter(
            is_active=True)  # Obtiene el QuerySet
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

    # debe ser solo para admins
    permission_classes = [permissions.IsAuthenticated]

    queryset = VehicleType.objects.all()
    serializer_class = VehicleTypeSerializer


class VehicleView(viewsets.ModelViewSet):
    serializer_class = VehicleSerializer
    queryset = Vehicle.objects.all()

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [permissions.AllowAny()]

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

    permission_classes = [permissions.AllowAny]  # admins

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
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        code = serializer.validated_data['code']

        pending = PendingUser.objects.filter(
            code=code,
            expires_at__gt=timezone.now()
        ).first()

        if not pending:
            return Response({"error": "Código inválido o expirado."},
                            status=status.HTTP_400_BAD_REQUEST)

        # SUBIR FOTO A CLOUDINARY SOLO SI EXISTE
        profile_image_url = None
        if pending.profile_image:
            upload_result = cloudinary.uploader.upload(pending.profile_image)
            profile_image_url = upload_result.get("secure_url")
        else:
            profile_image_url = settings.DEFAULT_PROFILE_IMAGE

        # Buscar si el usuario existía pero estaba inactivo
        existing_user = User.objects.filter(
            email=pending.email,
            is_active=False
        ).first()

        if existing_user:
            existing_user.is_active = True
            existing_user.name = pending.name
            existing_user.phone = pending.phone
            existing_user.password = pending.password
            existing_user.role_id = pending.role_id



            if profile_image_url:
                existing_user.profile_image = profile_image_url

            existing_user.save()

        else:
            if not pending.role_id:
                logger.error(f"PendingUser {pending.email} no tiene role_id asignado")
                return Response(
                    {"error": "Error: usuario pendiente sin rol asignado"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            user = User(
                name=pending.name,
                email=pending.email,
                phone=pending.phone,
                password=pending.password,  # ya hasheada
                role_id=pending.role_id,
                profile_image=profile_image_url,
                is_verified=True,
                username=pending.email
            )
            user.save()

        # BORRAR EL PENDINGUSER Y SU IMAGEN LOCAL
        pending.delete()

        return Response(
            {"message": "Usuario creado y verificado exitosamente."},
            status=status.HTTP_201_CREATED
        )


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
        reset_link = f"http://localhost:5173/confirm-reset-password?token={token}"

        # Enviar correo con el enlace de restablecimiento
        send_code_email(
            subject='Recuperación de contraseña - UniRide',
            message=(
                f'Hola {user.name},<br>'
                f'Solicitaste restablecer tu contraseña.<br>'
                f'Haz clic en el siguiente enlace para restablecer tu contraseña:<br>'
            ),
            finalmessage=(
                f'Este enlace expirará en 10 minutos.<br>'
                f'Si no solicitaste este cambio, ignora este mensaje.<br>'
                f'Gracias, el equipo de UniRide.'
            ),
            email=user.email,
            link_url=reset_link,
            link_text="Restablecer contraseña"
        )

        return Response({"message": "Se te ha enviado un codigo de recuperacion al correo."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(request_body=PasswordResetConfirmSerializer)
    def post(self, request):

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

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
        serializer = CambiarPasswordSerializer(
            data=request.data, context={'request': request})

        if serializer.is_valid():
            user = request.user

            if not user.check_password(serializer.validated_data['old_password']):
                return Response({"old_password": ["La contraseña actual es incorrecta."]}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return generar_respuesta_con_tokens(user, message="Contraseña actualizada y sesión renovada.")

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendNewVerificationCodeView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(request_body=ResendNewVerificationCodeSerializer)
    def post(self, request):

        serializer = ResendNewVerificationCodeSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = request.data.get('email')

        if not email:
            return Response({"error": "El campo email es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        # Verifica que no exista ya como usuario activo
        if User.objects.filter(email=email, is_active=True).exists():
            return Response({"error": "Este usuario ya está verificado."}, status=status.HTTP_400_BAD_REQUEST)

        # Buscar el PendingUser
        pending = PendingUser.objects.filter(email=email).first()
        if not pending:
            return Response({"error": "No se encontró un usuario pendiente con ese correo."}, status=status.HTTP_400_BAD_REQUEST)

        # Generar nuevo código
        new_code = generate_verification_code()

        # Actualizar el código y expiración
        pending.code = new_code
        pending.expires_at = timezone.now() + timedelta(minutes=15)
        pending.save()

        # Enviar el correo con el nuevo código
        send_code_email(
            subject="Nuevo Código de Verificación - UniRide",
            message=(
                f'Hola {pending.name},<br><br>'
                f'Tu código de verificación ha sido regenerado, '
                f'el nuevo código es:<br>'
            ),
            finalmessage=(
                f'Utiliza este código para completar tu registro. '
                f'Este código expirará en 10 minutos.<br><br>'
                f'Si no solicitaste este cambio, ignora este mensaje.<br><br>'
                f'Gracias, el equipo de UniRide.'
            ),
            email=pending.email,
            code=new_code
        )

        return Response({"message": "Se ha generado y enviado un nuevo código de verificación."}, status=status.HTTP_200_OK)


class ResendPasswordResetTokenView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(request_body=PasswordResetRequestSerializer)
    def post(self, request):

        serializer = PasswordResetRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = request.data.get('email')
        if not email:
            return Response({"error": "El campo email es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email, is_active=True).first()
        if not user:
            return Response({"error": "Usuario no encontrado o no activo."}, status=status.HTTP_400_BAD_REQUEST)

        # Generar un nuevo token de restablecimiento
        token = generate_reset_token(email)
        reset_link = f"https://app.unirideweb.online/reset-password?token={token}"

        # Enviar correo
        send_code_email(
            subject='Recuperación de contraseña (Nuevo link)- UniRide',
            message=(
                f'Hola {user.name},<br>'
                f'Tu link de recuperación de contraseña ha sido regenerado.<br>'
                f'Haz clic en el siguiente enlace para restablecer tu contraseña:<br>'
            ),
            finalmessage=(
                f'Este enlace expirará en 10 minutos.<br>'
                f'Si no solicitaste este cambio, ignora este mensaje.<br>'
                f'Gracias,<br>'
                f'El equipo de UniRide.'
            ),
            email=user.email,
            link_url=reset_link,
            link_text="Restablecer contraseña"
        )

        return Response({"message": "Se ha enviado un nuevo enlace para restablecer la contraseña."}, status=status.HTTP_200_OK)

# administrar usuarios admin

# 1. Filtrar Usuarios por correo o nombre 
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser
from django.db.models import Q

class AdminUserListView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer
    def get_queryset(self):
        search = self.request.query_params.get("search", "")

        queryset = User.objects.filter(
            is_active=True,
            is_staff=False
        )

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |   # 👈 CAMBIO CLAVE
                Q(email__icontains=search)
            )

        return queryset
# 2. Ver perfil completo del usuario + vehículos
from rest_framework.generics import RetrieveAPIView

class AdminUserDetailView(RetrieveAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminUserDetailSerializer
    queryset = User.objects.all()
    
# 3. Suspender usuario (soft delete)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta


from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

@api_view(['POST'])
@permission_classes([IsAdminUser])
def suspend_user(request, id):
    admin = request.user
    user = get_object_or_404(User, id=id)

    # ========================
    # DATOS
    # ========================
    complaint_ids = request.data.get('complaint_ids', [])
    is_permanent = request.data.get('is_permanent', False)
    days = request.data.get('days')
    reason = request.data.get('reason')

    # ========================
    # VALIDACIONES BÁSICAS
    # ========================
    if not complaint_ids:
        return Response(
            {"detail": "Debe seleccionar al menos una queja"},
            status=400
        )

    if not reason or not reason.strip():
        return Response(
            {"detail": "Debe indicar el motivo de la suspensión"},
            status=400
        )

    # ========================
    # VALIDAR QUEJAS DEL USUARIO
    # ========================
    complaints_qs = Complaint.objects.filter(
        id__in=complaint_ids,
        reported_user_id=user,   
        status_id=1              # pendiente
    )

    if not complaints_qs.exists():
        return Response(
            {"detail": "Las quejas seleccionadas no son válidas o no están activas"},
            status=400
        )

    # CONGELAR QUEJAS
    complaints = list(complaints_qs)

    # ========================
    # FECHAS
    # ========================
    start_date = timezone.now()
    end_date = None

    if not is_permanent:
        if not days:
            return Response(
                {"detail": "Debe indicar el número de días"},
                status=400
            )

        try:
            days = int(days)
        except (ValueError, TypeError):
            return Response(
                {"detail": "El número de días debe ser un entero"},
                status=400
            )

        if days < 1 or days > 365:
            return Response(
                {"detail": "Los días deben estar entre 1 y 365"},
                status=400
            )

        end_date = start_date + timedelta(days=days)

    # ========================
    # CREAR SUSPENSIÓN
    # ========================
    suspension = UserSuspension.objects.create(
        user_id=user,
        admin_id=admin,
        reason=reason,
        start_date=start_date,
        end_date=end_date,
        is_permanent=is_permanent
    )

    # ========================
    # DESACTIVAR USUARIO
    # ========================
    user.is_suspended = True
    user.save(update_fields=["is_suspended"])

    # ========================
    # MARCAR QUEJAS COMO RESUELTAS
    # ========================
    complaints_qs.update(
    status_id=2,
    resolved_at=timezone.now(),
    admin_id=admin
)
    # ========================
    # AUDITORÍA
    # ========================
    AuditLog.objects.create(
        actor=admin,
        action='SUSPENDER_USUARIO',
        target_user=user,
        reason=reason,
        extra_data={
            "complaint_ids": complaint_ids,
            "is_permanent": is_permanent,
            "days": days
        }
    )

    # ========================
    # CORREO
    # ========================
    send_suspension_email(
        user=user,
        complaints=complaints,  
        suspension=suspension
    )

    return Response(
        {"detail": "Usuario suspendido correctamente"},
        status=200
    )
