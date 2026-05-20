import pytest
from django.test import TestCase

@pytest.mark.django_db
class TestMatchBasics(TestCase):
    """Tests básicos para match"""
    
    def test_match_app_exists(self):
        """Test que app match existe"""
        from apps import match
        assert match is not None
