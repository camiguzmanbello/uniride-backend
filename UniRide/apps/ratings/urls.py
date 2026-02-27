from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RatingViewSet, GetAverageStarsUser

router = DefaultRouter()
router.register(r'ratings', RatingViewSet, basename='rating')

urlpatterns = [
    path('', include(router.urls)),
    path('average-stars/<int:user_id>/', GetAverageStarsUser.as_view(), name='average-stars'),
    
]