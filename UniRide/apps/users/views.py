from django.contrib.auth import authenticate
from django.utils.timezone import now
from rest_framework.views import APIView #Crear vistas basadas en clases (APIView) 
from rest_framework.response import Response #Retornar respuestas (Response) 
from rest_framework.permissions import IsAuthenticated #Definir quién puede acceder a cada vista (permissions)
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.conf import settings
from .serializer import LoginSerializer
from drf_yasg.utils import swagger_auto_schema
import logging

logger = logging.getLogger(__name__)

#Cuando se autentica un usuario se crea dos http seguras, 1 access token que dura 15min y un refresh token que dura 7 dias
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]

            user = authenticate(request, email=email, password=password)

            if user is not None:
                user.last_login = now()
                user.save(update_fields=["last_login"])

                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                response = Response({
                    "message": "Login exitoso",
                   # "rol": user.role_id.id no es necesario el token ya lo tiene 
                }, status=status.HTTP_200_OK)

                response.set_cookie(
                    key="access_token",
                    value=access_token,
                    httponly=True,
                    secure=True,  # En desarrollo se puede poner False si no se usa HTTPS
                    samesite="Lax",
                    max_age=60 * 15
                )
                response.set_cookie(
                    key="refresh_token",
                    value=refresh_token,
                    httponly=True,
                    secure=True,
                    samesite="Lax",
                    max_age=60 * 60 * 24 * 7  # 7 días
                )
                return response

            return Response(
                {"error": "Credenciales inválidas"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        except Exception as e:
            logger.error(f"Error interno durante el login: {str(e)}")
            return Response(
                {"error": "Error interno del servidor. Inténtalo más tarde."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
#Hace que elusuario no tenga que hacer el rpoceso de login ya que lo hace automaticamente 
class RefreshTokenView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token is None:
            return Response({"error": "Refresh token no encontrado"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            # Generar nuevo refresh token si ROTATE_REFRESH_TOKENS = True
            if settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS", False):
                new_refresh = str(refresh)
            else:
                new_refresh = refresh_token

            response = Response({"access_token": access_token})
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=True,
                samesite="Lax",
                max_age=60 * 15
            )
            
            response.set_cookie(
                key="refresh_token",
                value=new_refresh,
                httponly=True,
                secure=True,
                samesite="Lax",
                max_age=60 * 60 * 24 * 7  # 7 días
            )
            return response

        except TokenError:
            return Response({"error": "Token inválido o expirado"}, status=status.HTTP_401_UNAUTHORIZED)
        
class PerfilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "email": user.email,
            "name": user.name,
            "rol": user.role_id.name
        })
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