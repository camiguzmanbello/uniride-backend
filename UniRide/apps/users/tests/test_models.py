import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestUserBasics(TestCase):
    """Tests básicos para users - sin imports complejos"""
    
    def test_user_model_exists(self):
        """Test que User model existe"""
        assert User is not None
    
    def test_can_import_user(self):
        """Test que podemos importar User"""
        from apps.users.models import User as UserModel
        assert UserModel is not None
