from __future__ import annotations

import base64
import hashlib
import logging
import os

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

_fernet_instance: Fernet | None = None


def _derive_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def init_fernet(secret_key: str) -> None:
    global _fernet_instance
    key = _derive_fernet_key(secret_key)
    _fernet_instance = Fernet(key)
    logger.info("Fernet cipher initialized")


def _get_fernet() -> Fernet:
    if _fernet_instance is None:
        from app.core.config import get_settings

        settings = get_settings()
        init_fernet(settings.SECRET_KEY)
    return _fernet_instance


def encrypt_api_key(plaintext: str) -> str:
    if not plaintext:
        return ""
    f = _get_fernet()
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_api_key(ciphertext: str) -> str:
    if not ciphertext:
        return ""
    f = _get_fernet()
    try:
        return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except Exception:
        logger.warning("Failed to decrypt API key, returning empty string")
        return ""


def mask_api_key(key: str) -> str:
    if not key or len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]
