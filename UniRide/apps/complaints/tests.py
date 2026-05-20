import pytest
from django.test import TestCase

@pytest.mark.django_db
class TestComplaintsBasics(TestCase):
    """Tests básicos para complaints"""
    
    def test_complaints_app_exists(self):
        """Test que app complaints existe"""
        from apps import complaints
        assert complaints is not None
