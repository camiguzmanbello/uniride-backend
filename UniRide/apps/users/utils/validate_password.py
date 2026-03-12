from django.contrib.auth.password_validation import validate_password as django_validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

def validar_password_y_confirmacion(password1, password2, context_user=None):
    """
    Valida que dos contraseñas coincidan y que cumplan con las reglas de seguridad de Django.

    Args:
        password1 (str): Contraseña nueva.
        password2 (str): Confirmación de la contraseña.
        context_user (User): Usuario actual, para validaciones contextuales (como historial de contraseñas).

    Raises:
        serializers.ValidationError: Si hay errores de coincidencia o validación.

    Returns:
        str: La contraseña válida (password1).
    """
    if password1 != password2:
        raise serializers.ValidationError(_("Las contraseñas no coinciden."))

    try:
        django_validate_password(password1, user=context_user)
    except DjangoValidationError as e:
        errores = []
        for error in e.messages:
            if "too short" in error:
                errores.append(_("La contraseña es demasiado corta. Debe tener al menos 8 caracteres."))
            elif "too common" in error:
                errores.append(_("Esta contraseña es demasiado común."))
            elif "entirely numeric" in error:
                errores.append(_("Esta contraseña no puede ser completamente numérica."))
            elif "similar" in error:
                errores.append(_("La contraseña es demasiado parecida a tus datos personales. Usa algo más difícil de adivinar."))
            else:
                errores.append(error)
        raise serializers.ValidationError({"password": errores})

    return password1
