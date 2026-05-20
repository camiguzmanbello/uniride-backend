import pytest
from django.test import TestCase

@pytest.mark.django_db
class TestTripsBasics(TestCase):
    """Tests básicos para trips"""
    
    def test_trips_app_exists(self):
        """Test que app trips existe"""
        from apps import trips
        assert trips is not None
