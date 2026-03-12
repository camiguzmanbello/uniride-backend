from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Creates a superuser non-interactively if it does not exist'

    def handle(self, *args, **options):
        User = get_user_model()
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        name = os.environ.get('DJANGO_SUPERUSER_NAME', 'Admin')
        phone = os.environ.get('DJANGO_SUPERUSER_PHONE', '0000000000')

        if not email or not password:
            self.stdout.write(self.style.WARNING('DJANGO_SUPERUSER_EMAIL or DJANGO_SUPERUSER_PASSWORD not set. Skipping superuser creation.'))
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.SUCCESS(f'Superuser {email} already exists.'))
        else:
            User.objects.create_superuser(email=email, password=password, name=name, phone=phone)
            self.stdout.write(self.style.SUCCESS(f'Superuser {email} created successfully.'))
