import os
from django.conf import settings
from django.contrib.staticfiles import finders

def link_callback(uri, rel):
    """
    Convierte rutas de static en rutas reales del sistema
    para que xhtml2pdf pueda leerlas.
    """
    # Buscar en staticfiles
    result = finders.find(uri)
    if result:
        if isinstance(result, (list, tuple)):
            result = result[0]
        return result

    # Si no se encuentra
    raise Exception(f"Archivo no encontrado: {uri}")
