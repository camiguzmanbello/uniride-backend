from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import * 

router = DefaultRouter() 
urlpatterns = [
    path("dashboard/", AdminDashboardView.as_view()),
    # Hacer que solo las pueda ver el admin

    path("report/users/preview/", user_preview, name="user-preview"),
    path("report/users/pdf/", UserReportPDFView.as_view()),
    path("report/trips/preview/", TripReportPreviewView.as_view()),
    path("report/trips/pdf/", TripReportPDFView.as_view()),
    path("report/ratings/preview/", rating_preview, name="rating-preview"),
    path("report/ratings/pdf/", RatingReportPDFView.as_view()),
    path("report/complaints/preview/", complaint_preview, name="complaint-preview"),
    path("report/complaints/pdf/", ComplaintReportPDFView.as_view()),
    path("report/audit-logs/preview/", audit_preview, name="audit-preview"),
    path("report/audit-logs/pdf/", AuditReportPDFView.as_view()),
    path("report/suspensions/preview/", suspension_preview, name="suspension-preview"),
    path("report/suspensions/pdf/", SuspensionReportPDFView.as_view()),
 

]
