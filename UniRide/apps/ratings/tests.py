import pytest
from django.test import TestCase

@pytest.mark.django_db
class TestRatingsBasics(TestCase):
    """Tests básicos para ratings"""
    
    def test_ratings_app_exists(self):
        """Test que app ratings existe"""
        from apps import ratings
        assert ratings is not None
