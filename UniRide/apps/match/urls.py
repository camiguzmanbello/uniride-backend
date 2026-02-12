from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import * 

router = DefaultRouter() 
urlpatterns = [
    path("generate-suggestion/", GenerateSuggestionsView.as_view()),
    path("my-suggestions/", GetMySuggestionsView.as_view()),

    

]
