from django.db import migrations

def populate_complaints(apps, schema_editor):
    ComplaintType = apps.get_model('complaints', 'ComplaintType')
    ComplaintStatus = apps.get_model('complaints', 'ComplaintStatus')

    # ComplaintType data
    types = [
        {"name": "Comportamiento", "description": "Conducta inapropiada del usuario"},
        {"name": "Técnica", "description": "Problemas durante el viaje"},
    ]
    
    for t in types:
        ComplaintType.objects.get_or_create(name=t["name"], defaults={'description': t["description"]})

    # ComplaintStatus data
    statuses = [
        {"name": "Pendiente"},
        {"name": "Resuelta"},
    ]
    
    for s in statuses:
        ComplaintStatus.objects.get_or_create(name=s["name"])

class Migration(migrations.Migration):

    dependencies = [
        ('complaints', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(populate_complaints),
    ]
