import hashlib
import os
import hmac

SALT_LENGTH = 32
ITERATIONS = 100000


def hash_password(password: str) -> str:
    salt = os.urandom(SALT_LENGTH)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        ITERATIONS
    )
    return f"{salt.hex()}:{key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, key_hex = stored_hash.split(':')
        salt = bytes.fromhex(salt_hex)
        stored_key = bytes.fromhex(key_hex)
        
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            ITERATIONS
        )
        
        return hmac.compare_digest(new_key, stored_key)
    except Exception:
        return False
