import base64
import json
from functools import lru_cache
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, load_pem_private_key
from django.conf import settings


class LoginPayloadDecryptionError(Exception):
    pass


def _normalize_pem(pem: str) -> bytes:
    if not pem:
        return b""
    pem = pem.strip().replace("\\n", "\n")
    return pem.encode("utf-8")


@lru_cache(maxsize=2)
def _get_login_private_key():
    pem = getattr(settings, "LOGIN_PAYLOAD_PRIVATE_KEY_PEM", "")
    pem_bytes = _normalize_pem(pem)
    if not pem_bytes:
        return None
    return load_pem_private_key(pem_bytes, password=None)


def get_login_public_key_pem() -> str:
    public_pem = getattr(settings, "LOGIN_PAYLOAD_PUBLIC_KEY_PEM", "")
    if public_pem:
        return _normalize_pem(public_pem).decode("utf-8")

    private_key = _get_login_private_key()
    if private_key is None:
        return ""

    public_key = private_key.public_key()
    return public_key.public_bytes(encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo).decode("utf-8")


def _b64decode(value: Any) -> bytes:
    if not isinstance(value, str) or not value:
        raise LoginPayloadDecryptionError()
    try:
        return base64.b64decode(value, validate=True)
    except Exception as e:
        raise LoginPayloadDecryptionError() from e


def decrypt_login_payload(payload: Any) -> dict[str, str]:
    if not isinstance(payload, dict):
        raise LoginPayloadDecryptionError()

    if payload.get("v") != 1:
        raise LoginPayloadDecryptionError()

    if payload.get("alg") != "RSA-OAEP-256+A256GCM":
        raise LoginPayloadDecryptionError()

    enc_key = _b64decode(payload.get("enc_key"))
    iv = _b64decode(payload.get("iv"))
    ciphertext = _b64decode(payload.get("ciphertext"))

    if len(iv) != 12:
        raise LoginPayloadDecryptionError()

    private_key = _get_login_private_key()
    if private_key is None:
        raise LoginPayloadDecryptionError()

    try:
        aes_key = private_key.decrypt(
            enc_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
    except Exception as e:
        raise LoginPayloadDecryptionError() from e

    if len(aes_key) != 32:
        raise LoginPayloadDecryptionError()

    try:
        plaintext_bytes = AESGCM(aes_key).decrypt(iv, ciphertext, None)
    except Exception as e:
        raise LoginPayloadDecryptionError() from e

    try:
        decoded = json.loads(plaintext_bytes.decode("utf-8"))
    except Exception as e:
        raise LoginPayloadDecryptionError() from e

    if not isinstance(decoded, dict):
        raise LoginPayloadDecryptionError()

    email = decoded.get("email")
    password = decoded.get("password")

    if not isinstance(email, str) or not isinstance(password, str):
        raise LoginPayloadDecryptionError()

    return {"email": email, "password": password}
