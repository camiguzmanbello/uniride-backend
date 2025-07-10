from django.urls import path
from .views import LoginView, PerfilView, LogoutView, RefreshTokenView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("perfil/", PerfilView.as_view(), name="perfil"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh-token/", RefreshTokenView.as_view(), name="refresh_token"),
]
