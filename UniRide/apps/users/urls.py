from django.urls import path
from .views import LoginView, PerfilView, LogoutView, RefreshTokenView, CambiarPasswordView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("refresh-token/", RefreshTokenView.as_view(), name="refresh_token"),
    path("perfil/", PerfilView.as_view(), name="perfil"),
    path('perfil/cambiar-password/', CambiarPasswordView.as_view()),  
    path("logout/", LogoutView.as_view(), name="logout"),
    
    
]
