import re
import cloudinary
import cloudinary.uploader
from typing import Optional

def extract_public_id_from_url(image_url: str) -> Optional[str]:
    """
    Extrae el public_id de una URL de Cloudinary de manera más robusta.
    """
    if not image_url:
        return None
    
    try:
        # Buscar el public_id después de /upload/
        # Ejemplo: https://res.cloudinary.com/demo/image/upload/v1234567/folder/image.jpg
        # Extraerá: folder/image
        pattern = r'/upload/(?:v\d+/)?(.+?)(?:\.\w+)?$'
        match = re.search(pattern, image_url)
        
        if match:
            public_id = match.group(1)
            # Limpiar posibles parámetros de transformación
            if '/' in public_id:
                # Eliminar transformaciones si existen (ej: c_fill,w_100,h_100/folder/image)
                if public_id.startswith('c_'):
                    parts = public_id.split('/')
                    if len(parts) > 1:
                        public_id = '/'.join(parts[1:])
            return public_id
    except Exception:
        pass
    return None

def delete_cloudinary_image(image_url: str | None):
    """
    Elimina una imagen de Cloudinary dada su URL.
    """
    public_id = extract_public_id_from_url(image_url)
    
    if not public_id:
        print(f"No se pudo extraer public_id de: {image_url}")
        return
    
    try:
        # Forzar eliminación incluso si hay derivadas
        result = cloudinary.uploader.destroy(
            public_id,
            invalidate=True  # Invalidar CDN
        )
        if result.get('result') == 'ok':
            print(f"✅ Imagen eliminada: {public_id}")
        else:
            print(f"⚠️ No se pudo eliminar imagen: {public_id}, resultado: {result}")
    except Exception as e:
        print(f"❌ Error eliminando imagen {public_id}: {e}")

def replace_user_image(old_image_url: str | None, new_image_file):
    """
    Reemplaza la imagen de un usuario:
    - Elimina la imagen anterior (si existe)
    - Sube la nueva
    - Retorna secure_url de la nueva imagen
    """
    # 1. Eliminar anterior
    delete_cloudinary_image(old_image_url)

    # 2. Subir nueva
    try:
        upload = cloudinary.uploader.upload(
            new_image_file,
            folder="profile_pictures"
        )
        return upload.get("secure_url")
    except Exception as e:
        print(f"Error subiendo nueva imagen: {e}")
        return None
