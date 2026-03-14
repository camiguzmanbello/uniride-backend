from django.db import migrations

def populate_trips_data(apps, schema_editor):
    PublicationType = apps.get_model('trips', 'PublicationType')
    TripPassengerStatus = apps.get_model('trips', 'TripPassengerStatus')
    TripStatus = apps.get_model('trips', 'TripStatus')

    # PublicationType
    # id, name
    pub_types = [
        (1, "Solicitud"),
        (2, "Oferta"),
    ]
    
    for pk, name in pub_types:
        if not PublicationType.objects.filter(pk=pk).exists():
            PublicationType.objects.create(pk=pk, name=name)
        elif not PublicationType.objects.filter(pk=pk, name=name).exists():
            # If exists but name is different, we might want to update it or leave it.
            # For safety in migration, usually better to leave it or update if we are sure.
            # Here we just ensure the ID exists with that name if it didn't exist.
            pass

    # TripPassengerStatus
    # id, name
    passenger_statuses = [
        (1, "Aceptado"),
        (2, "Finalizado"),
        (3, "Cancelado"),
        (4, "Pendiente"),
    ]
    
    for pk, name in passenger_statuses:
        if not TripPassengerStatus.objects.filter(pk=pk).exists():
            TripPassengerStatus.objects.get_or_create(pk=pk, defaults={'name': name})

    # TripStatus
    # id, name
    trip_statuses = [
        (1, "Pendiente"), # Corregido de 'Peniente'
        (2, "En curso"),
        (3, "Finalizado"),
        (4, "Cancelado"),
    ]
    
    for pk, name in trip_statuses:
        if not TripStatus.objects.filter(pk=pk).exists():
            TripStatus.objects.get_or_create(pk=pk, defaults={'name': name})

class Migration(migrations.Migration):

    dependencies = [
        ('trips', '0007_trip_updated_at'),
    ]

    operations = [
        migrations.RunPython(populate_trips_data),
    ]
