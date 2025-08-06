from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import * 

router = DefaultRouter()
router.register(r'vehicle-types', VehicleTypeView, basename='vehicle-types')
router.register(r'vehicles', VehicleView, basename='vehicles')

urlpatterns = [
    path('', include(router.urls)),
    path("Login/", LoginView.as_view(), name="login"),
    path("Refresh-token/", RefreshTokenView.as_view(), name="refresh_token"),
    path('me/', UserMeView.as_view(), name='user-me'),
    path("Admin/perfil/", PerfilView.as_view(), name="perfil"),
    path('Change-password/', CambiarPasswordView.as_view()),  
    path("Logout/", LogoutView.as_view(), name="logout"),
    path("Admin/register/", PreRegisterAdminView.as_view(), name="register_admin"),
    path("ConfirmRegisterAdmin/", ConfirmAdminView.as_view(), name="confirm_admin"),
    path("Users/", UserView.as_view(), name="registrerUser"),
    path("roles/", RoleView.as_view(), name="roles"),
    path('UserActions/<int:pk>/', UserEditDeleteView.as_view(), name='user_detail_edit_delete'),
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-pending/', VerifyPendingUserView.as_view(), name='verify_pending'),
    path('pending-users/<int:pk>/', UserPendingEditDeleteView.as_view(), name='pending_user_detail_edit_delete'),
    path('pending-users/', UserPendingView.as_view(), name='pending_users'),
    path('auth/request-password-reset/', PasswordResetRequestView.as_view(), name='request-password-reset'),
    path('auth/confirm-password-reset/', PasswordResetConfirmView.as_view(), name='confirm-password-reset'),
    path('user-profile/', UserSelfProfileView.as_view(), name='user_profile'),
    path('user-vehicles/', UserVehicleProfileView.as_view(), name='user_vehicles'),
    path("user-vehicles/<int:vehicle_id>/deactivate/", DeactivateSingleVehicleView.as_view(), name="deactivate-vehicle"),
    path("user-vehicles/deactivate-all/", DeactivateAllVehiclesView.as_view(), name="deactivate-all-vehicles"),
    path('register/resend-verification-code/', ResendNewVerificationCodeView.as_view(), name='resend-verification-code'),
    path('auth/resend-password-reset/', ResendPasswordResetTokenView.as_view(), name='resend-password-reset'),
]
