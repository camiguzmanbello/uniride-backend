from django.db import migrations

def populate_users_data(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    VehicleType = apps.get_model('users', 'VehicleType')

    # Role
    # id, name
    roles = [
        (1, "Administrador"),
        (2, "Usuario"),
    ]
    
    for pk, name in roles:
        if not Role.objects.filter(pk=pk).exists():
            Role.objects.get_or_create(pk=pk, defaults={'name': name})
        elif not Role.objects.filter(pk=pk, name=name).exists():
            pass

    # VehicleType
    # id, name
    vehicle_types = [
        (1, "Moto"),
        (2, "Carro"),
    ]
    
    for pk, name in vehicle_types:
        if not VehicleType.objects.filter(pk=pk).exists():
            VehicleType.objects.get_or_create(pk=pk, defaults={'name': name})

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_user_is_suspended'),
    ]

    operations = [
        migrations.RunPython(populate_users_data),
    ]
