from django.contrib.auth import authenticate
from django.utils.timezone import now
from rest_framework.views import APIView #Crear vistas basadas en clases (APIView) 
from rest_framework.response import Response #Retornar respuestas (Response) 
from rest_framework.permissions import IsAuthenticated #Definir quién puede acceder a cada vista (permissions)
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.conf import settings
from .serializer import LoginSerializer, CambiarPasswordSerializer, EditarPerfilSerializer
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import get_user_model
import logging
from rest_framework.exceptions import ValidationError
User = get_user_model()
logger = logging.getLogger(__name__)
from .utils.jwt_cookies import generar_respuesta_con_tokens, set_tokens_en_response
from .utils.audit import registrar_log

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data["email"]
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
    permission_classes = [IsAuthenticated]

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


#Borra ambas cookies 
class LogoutView(APIView):
    permission_classes = [IsAuthenticated] 

    def post(self, request):
        try:
            response = Response({"message": "Logout exitoso"}, status=status.HTTP_200_OK)
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")
            return response
        except Exception as e:
            logger.error(f"Error durante logout: {str(e)}")
            return Response(
                {"error": "Ocurrió un error durante el logout. Inténtalo más tarde."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
