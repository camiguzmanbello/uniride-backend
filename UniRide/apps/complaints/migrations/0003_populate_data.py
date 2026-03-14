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
        if not ComplaintType.objects.filter(name=t["name"]).exists():
            ComplaintType.objects.create(name=t["name"], description=t["description"])

    # ComplaintStatus data
    statuses = [
        {"name": "Pendiente"},
        {"name": "Resuelta"},
    ]
    
    for s in statuses:
        if not ComplaintStatus.objects.filter(name=s["name"]).exists():
            ComplaintStatus.objects.create(name=s["name"])

class Migration(migrations.Migration):

    dependencies = [
        ('complaints', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(populate_complaints),
    ]
