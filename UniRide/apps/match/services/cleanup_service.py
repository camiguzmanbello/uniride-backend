from match.models import MatchSuggestion

def deactivate_suggestions_for_inactive_publications():
    """
    Desactiva sugerencias cuando una publicación deja de estar activa.
    """
    MatchSuggestion.objects.filter(
        driver_publication__is_active=False
    ).update(is_active=False)
