import pytest
from django.test import TestCase

@pytest.mark.django_db
class TestCoreBasics(TestCase):
    """Tests básicos para core"""
    
    def test_core_app_exists(self):
        """Test que app core existe"""
        from apps import core
        assert core is not None
