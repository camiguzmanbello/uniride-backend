from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatViewSet, InterestViewSet

router = DefaultRouter()
router.register(r'chats', ChatViewSet, basename='chat')
router.register(r'interests', InterestViewSet, basename='interest')

urlpatterns = [
    path('', include(router.urls)),
]
