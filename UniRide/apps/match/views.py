from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.match.models import MatchSuggestion
from apps.match.services.matching_service import generate_suggestions_for_driver
from apps.trips.models import Publication
from apps.match.models import MatchSuggestion
from apps.match.services.grouping_service import build_groups_from_suggestions

class GenerateSuggestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        publications = Publication.objects.filter(
            user_id=request.user,
            type_id=2,
            is_active=True
        )

        if not publications.exists():
            return Response(
                {"detail": "No tienes publicaciones activas como conductor"},
                status=400
            )

        for pub in publications:
            generate_suggestions_for_driver(pub)

        return Response(
            {"message": "Sugerencias generadas correctamente"}
        )

class GetMySuggestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retorna las sugerencias activas del conductor autenticado
        para TODAS sus publicaciones activas.
        """

        driver_publications = Publication.objects.filter(
            user_id=request.user,
            type_id=2,        # Conductor
            is_active=True
        )

        if not driver_publications.exists():
            return Response(
                {"message": "No tienes publicaciones activas como conductor"},
                status=400
            )

        suggestions = (
            MatchSuggestion.objects
            .filter(
                driver_publication__in=driver_publications,
                is_active=True
            )
            .select_related(
                "driver_publication",
                "passenger_publication"
            )
            .order_by("-score")
        )

        if not suggestions.exists():
            return Response(
                {
                    "message": "No hay pasajeros sugeridos por ahora",
                    "results": []
                }
            )

        results = {}

        for suggestion in suggestions:
            driver_pub = suggestion.driver_publication
            passenger = suggestion.passenger_publication

            pub_id = driver_pub.id

            if pub_id not in results:
                results[pub_id] = {
                    "driver_publication": {
                        "publication_id": driver_pub.id,
                        "departure_place": driver_pub.departure_place,
                        "destination": driver_pub.destination,
                        "departure_datetime": driver_pub.departure_datetime,
                    },
                    "suggestions": []
                }

            results[pub_id]["suggestions"].append({
                "suggestion_id": suggestion.id,
                "score": suggestion.score,
                "passenger": {
                    "name": passenger.user_id.name,
                    "publication_id": passenger.id,
                    "departure_place": passenger.departure_place,
                    "destination": passenger.destination,
                    "departure_datetime": passenger.departure_datetime,
                }
            })

        return Response(
            {
                "total_publications": driver_publications.count(),
                "results": list(results.values())
            }
        )

class HasDriverPublicationView(APIView):
    permission_classes=[IsAuthenticated]

    def get(self, request):
        exists = Publication.objects.filter(
            user_id=request.user,
            type_id=2, # Conductor
            is_active=True
        ).exists()

        return Response({"has_active": exists})



class IgnoreSuggestionView(APIView):
    permission_classes=[IsAuthenticated]

    def patch(self, request, pk):
        try:
            suggestion = MatchSuggestion.objects.get(
                id=pk,
                driver_publication__user_id=request.user
            )

            suggestion.is_active = False
            suggestion.save()

            return Response({"message":"Sugerencia ignorada"})
        
        except MatchSuggestion.DoesNotExist:
            return Response({"error":"No encontrada"}, status=404)


class GetSuggestionGroupsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        driver_publications = Publication.objects.filter(
            user_id=request.user,
            type_id=2,
            is_active=True
        )

        suggestions = (
            MatchSuggestion.objects
            .filter(
                driver_publication__in=driver_publications,
                is_active=True
            )
            .select_related("passenger_publication")
        )

        groups = build_groups_from_suggestions(suggestions)

        return Response({
            "groups": groups
        })