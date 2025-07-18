from rest_framework.serializers import ValidationError
from django.core.validators import validate_email as django_validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
import re
from rest_framework.serializers import ValidationError

def validate_name(name: str) -> str:
    if not name:
        raise ValidationError("El nombre no puede estar vacío.")

    if len(name) > 100:
        raise ValidationError("El nombre no debe superar los 100 caracteres.")

    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$', name):
        raise ValidationError("El nombre solo puede contener letras y espacios.")

    return name.strip()

def validate_phone_number(phone: str) -> str:
    if not phone:
        raise ValidationError("El número telefónico no puede estar vacío.")

    if not phone.isdigit():
        raise ValidationError("El número telefónico solo debe contener dígitos.")

    if not (8 <= len(phone) <= 10):
        raise ValidationError("El número telefónico debe tener entre 8 y 10 dígitos.")

    return phone

def validate_email(email: str) -> str:
    if not email:
        raise ValidationError("El correo electrónico no puede estar vacío.")
    
    email = email.strip()
    
    try:
        django_validate_email(email)
    except DjangoValidationError:
        raise ValidationError("El formato del correo electrónico no es válido.")

    return email.lower()