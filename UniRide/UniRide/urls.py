
from django.contrib import admin
from django.urls import path, re_path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings

# Configuración Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="UniRide API",
        default_version='v1',
        description="Documentación interactiva de la API UniRide",
        contact=openapi.Contact(email="soporte@uniride.com"),
        license=openapi.License(name="MIT"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/users/", include("apps.users.urls")),
    path("api/trips/", include("apps.trips.urls")),
    path("api/chat/", include("apps.chat.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    
]

# Mostrar Swagger solo en modo DEBUG
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ]
