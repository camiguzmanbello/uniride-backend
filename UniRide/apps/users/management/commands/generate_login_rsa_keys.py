from django.core.management.base import BaseCommand

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


class Command(BaseCommand):
    help = "Genera un par de llaves RSA para cifrado del payload de login (RSA-OAEP-256 + AES-256-GCM)."

    def add_arguments(self, parser):
        parser.add_argument("--bits", type=int, default=3072)

    def handle(self, *args, **options):
        bits = int(options["bits"])
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        self.stdout.write("PRIVATE KEY (PEM):")
        self.stdout.write(private_pem)
        self.stdout.write("PUBLIC KEY (PEM):")
        self.stdout.write(public_pem)

        self.stdout.write("ENV (una línea, con \\n escapado):")
        self.stdout.write(f"LOGIN_PAYLOAD_PRIVATE_KEY_PEM={private_pem.strip().replace(chr(10), r'\\n')}")
        self.stdout.write(f"LOGIN_PAYLOAD_PUBLIC_KEY_PEM={public_pem.strip().replace(chr(10), r'\\n')}")
