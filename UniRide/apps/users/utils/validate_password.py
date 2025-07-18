# dev/validate/password.py
from django.contrib.auth.password_validation import validate_password as django_validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

def validar_password_y_confirmacion(data, context_user=None):
    """
    Valida la contraseña nueva (seguridad y coincidencia con confirmación).
    Lanza serializers.ValidationError si hay errores.
    """
    password = data.get("new_password") or data.get("password")
    confirm = data.get("confirm_password")

    if password != confirm:
        raise serializers.ValidationError(_("Las contraseñas no coinciden."))

    try:
        django_validate_password(password, user=context_user)
    except DjangoValidationError as e:
        errores = []
        for error in e.messages:
            if "too short" in error:
                errores.append(_("La contraseña es demasiado corta. Debe tener al menos 8 caracteres."))
            elif "too common" in error:
                errores.append(_("Esta contraseña es demasiado común."))
            elif "entirely numeric" in error:
                errores.append(_("Esta contraseña no puede ser completamente numérica."))
            else:
                errores.append(error)
        raise serializers.ValidationError({"new_password": errores})

    return data