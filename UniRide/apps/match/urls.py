from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import * 

router = DefaultRouter() 
urlpatterns = [
    path("generate-suggestion/", GenerateSuggestionsView.as_view()),
    path("my-suggestions/", GetMySuggestionsView.as_view()),
    path("my-driver-publications/", HasDriverPublicationView.as_view()),
    path("suggestions/<int:pk>/ignore/", IgnoreSuggestionView.as_view()),
    path("suggestion-groups/",GetSuggestionGroupsView.as_view()),
]
