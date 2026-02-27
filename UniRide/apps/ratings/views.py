from rest_framework import viewsets, views
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Avg
from .models import Rating
from .serializers import RatingSerializer

class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer

class GetAverageStarsUser(views.APIView):
    def get(self, request, user_id, format=None):
        if user_id is None:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_id = int(user_id)
        except ValueError:
            return Response({'error': 'user_id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
        average_stars = Rating.objects.filter(reviewed_id=user_id).aggregate(Avg('stars'))['stars__avg']
        if average_stars is None:
            average_stars = 0
        return Response({'average_stars': average_stars}, status=status.HTTP_200_OK)

