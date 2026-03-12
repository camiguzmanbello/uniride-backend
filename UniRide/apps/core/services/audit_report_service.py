from collections import defaultdict
def humanize_user_agent(ua: str):
    if not ua:
        return "Desconocido"

    ua = ua.lower()

    browser = "Navegador desconocido"
    os = "SO desconocido"

    if "chrome" in ua and "edg" not in ua:
        browser = "Chrome"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Safari"
    elif "edg" in ua:
        browser = "Edge"

    if "windows" in ua:
        os = "Windows"
    elif "android" in ua:
        os = "Android"
    elif "iphone" in ua or "ipad" in ua:
        os = "iOS"
    elif "mac os" in ua or "macintosh" in ua:
        os = "macOS"
    elif "linux" in ua:
        os = "Linux"

    return f"{browser} · {os}"

# 🔹 Labels humanos para las acciones
ACTION_LABELS = {
    "LOGIN_EXITOSO": "Inicio de sesión exitoso",
    "LOGIN_FALLIDO": "Intento de inicio de sesión fallido",
    "ACTUALIZAR_PERFIL": "Actualización de perfil",
    "ACCION_REGISTRO_ADMIN": "Registro de administrador",
    "SOFT_DELETE_ADMIN": "Desactivación de administrador",
    "SUSPENDER_USUARIO": "Suspensión de usuario",
    "RESOLVER_QUEJA": "Resolución de queja",
    "LOGIN_BLOQUEADO_SUSPENSION": "Inicio de sesión bloqueado por suspensión",
}

# 🔹 Labels humanos para campos de perfil
PROFILE_FIELD_LABELS = {
    "name": "Nombre",
    "phone": "Teléfono",
    "profile_image": "Foto de perfil",
    "password": "Contraseña",
    "email": "Correo electrónico",
}


def format_extra_data(action, extra_data):
    if not extra_data:
        return []

    formatted = []

    if action == "LOGIN_EXITOSO":
        formatted.append(f"IP: {extra_data.get('ip')}")
        formatted.append(
            f"Dispositivo: {humanize_user_agent(extra_data.get('user_agent'))}"
        )


    elif action == "LOGIN_FALLIDO":
        formatted.append(f"IP: {extra_data.get('ip')}")
        formatted.append(f"Correo ingresado: {extra_data.get('email')}")
        formatted.append(f"Error: {extra_data.get('error')}")

    elif action == "ACTUALIZAR_PERFIL":
        cambios = extra_data.get("cambios", {})

        for field in cambios.keys():
            label = PROFILE_FIELD_LABELS.get(field, field)
            formatted.append(f"{label} actualizado")

    elif action == "SUSPENDER_USUARIO":
        if extra_data.get("is_permanent"):
            formatted.append("Suspensión permanente")
        else:
            formatted.append(f"Días de suspensión: {extra_data.get('days')}")

        ids = extra_data.get("complaint_ids", [])
        if ids:
            formatted.append(f"Quejas relacionadas: {', '.join(map(str, ids))}")

    elif action == "RESOLVER_QUEJA":
        formatted.append(f"Tipo de queja: {extra_data.get('type')}")
        formatted.append(f"ID de queja: {extra_data.get('complaint_id')}")

    elif action == "LOGIN_BLOQUEADO_SUSPENSION":
        formatted.append(f"Motivo: {extra_data.get('reason')}")
        formatted.append(f"Días restantes: {extra_data.get('remaining_days')}")

    return formatted

def group_audit_logs(logs):
    """
    Agrupa logs por acción y devuelve datos listos para preview y PDF.
    """
    grouped = defaultdict(list)

    for l in logs:
        label = ACTION_LABELS.get(l.action, l.action)

        grouped[label].append({
            "actor": l.actor.email if l.actor else "Sistema",
            "target": l.target_user.email if l.target_user else None,
            "reason": l.reason,
            "extra_data": format_extra_data(l.action, l.extra_data),
            "date": l.timestamp,
        })


    return grouped

