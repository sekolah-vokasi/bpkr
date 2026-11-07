import base64
import binascii
import hashlib
import hmac
import json
import os
import secrets
import time
from fastapi import HTTPException

TOKEN_SECRET = os.environ.get("BPKR_SECRET", "")
if len(TOKEN_SECRET) < 32:
    raise RuntimeError("BPKR_SECRET harus berupa nilai acak minimal 32 karakter")

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return "scrypt$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(digest).decode()

def verify_password(password: str, encoded: str) -> bool:
    try:
        _, salt, digest = encoded.split("$", 2)
        actual = hashlib.scrypt(password.encode(), salt=base64.urlsafe_b64decode(salt), n=16384, r=8, p=1)
        return hmac.compare_digest(actual, base64.urlsafe_b64decode(digest))
    except (ValueError, TypeError):
        return False

def create_token(user_id: int, token_version: str) -> str:
    payload = {"sub": user_id, "ver": token_version, "exp": int(time.time()) + 8 * 3600}
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(TOKEN_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    return body + "." + signature

def read_token(token: str) -> dict:
    try:
        body, signature = token.split(".", 1)
        valid = hmac.new(TOKEN_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, valid):
            raise ValueError("signature")
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        if int(payload["exp"]) <= time.time():
            raise ValueError("expired")
        return payload
    except (ValueError, KeyError, TypeError, json.JSONDecodeError, binascii.Error):
        raise HTTPException(status_code=401, detail="Sesi tidak valid atau kedaluwarsa")
