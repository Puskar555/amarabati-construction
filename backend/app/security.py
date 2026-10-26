"""Deterministic security helpers; never accept client-side roles/prices as trusted."""
import base64
import hashlib
import hmac
import secrets
import struct
import time
from typing import Optional

ROLES = {'customer', 'regional_admin', 'super_admin'}
EVENT_TYPES = {
    'page_viewed', 'product_searched', 'product_clicked', 'price_viewed',
    'cart_item_added', 'cart_item_removed', 'plan_started', 'material_compared',
    'estimate_created',
}
EVENT_KEYS = {'page', 'query', 'product_id', 'category', 'result_count', 'quantity', 'plan_type'}

def hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or secrets.token_hex(16)
    result = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1, dklen=32)
    return f'scrypt$16384$8$1${salt}${result.hex()}'

def verify_password(password: str, stored: str) -> bool:
    try:
        alg, n, r, p, salt, expected = stored.split('$')
        if alg != 'scrypt': return False
        result = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p), dklen=32)
        return hmac.compare_digest(result.hex(), expected)
    except (ValueError, TypeError):
        return False

def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip('=')

def totp(secret: str, at: int | None = None) -> str:
    at = int(time.time() if at is None else at)
    key = base64.b32decode(secret.upper() + '=' * (-len(secret) % 8))
    digest = hmac.new(key, struct.pack('>Q', at // 30), hashlib.sha1).digest()
    offset = digest[-1] & 15
    return str((struct.unpack('>I', digest[offset:offset+4])[0] & 0x7fffffff) % 1_000_000).zfill(6)

def verify_totp(secret: str | None, code: str | None, at: int | None = None) -> bool:
    if not secret or not code or not (len(code)==6 and code.isascii() and code.isdigit()): return False
    at = int(time.time() if at is None else at)
    return any(hmac.compare_digest(totp(secret, at + diff*30), code) for diff in [-1,0,1])

def encrypt_secret(plaintext: str, encryption_key: str) -> str:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = base64.urlsafe_b64decode(encryption_key)
    nonce = secrets.token_bytes(12)
    encrypted = AESGCM(key).encrypt(nonce, plaintext.encode(), None)
    return base64.urlsafe_b64encode(nonce + encrypted).decode()

def decrypt_secret(ciphertext: str, encryption_key: str) -> str:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = base64.urlsafe_b64decode(encryption_key)
    raw = base64.urlsafe_b64decode(ciphertext)
    return AESGCM(key).decrypt(raw[:12], raw[12:], None).decode()

def can_access_region(role: str, actor_region: str | None, resource_region: str | None) -> bool:
    return role == 'super_admin' or (role == 'regional_admin' and bool(actor_region) and actor_region == resource_region)

def clean_event(event_name: str, details: dict) -> dict:
    if event_name not in EVENT_TYPES: raise ValueError('Event type not permitted')
    if not isinstance(details, dict) or len(details) > 8: raise ValueError('Invalid event data')
    if any(key not in EVENT_KEYS for key in details): raise ValueError('Unrecognized event field')
    safe = {}
    for key, val in details.items():
        if not isinstance(val, (int, float, str, bool)) or len(str(val)) > 120:
            raise ValueError('Invalid event field value')
        safe[key] = val
    return safe
