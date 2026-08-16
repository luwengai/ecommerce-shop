"""安全模块：自写 HMAC-SHA256 JWT + PBKDF2 密码哈希（零第三方依赖）"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time

SECRET_KEY = os.environ.get("SHOP_SECRET_KEY", "ecommerce-shop-dev-secret-key-change-me")
TOKEN_TTL_HOURS = 24


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)


def create_token(payload: dict, expires_hours: int = TOKEN_TTL_HOURS) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    body = dict(payload)
    body["exp"] = int(time.time()) + expires_hours * 3600
    header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    body_b64 = _b64url(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    msg = f"{header_b64}.{body_b64}".encode("utf-8")
    sig = hmac.new(SECRET_KEY.encode("utf-8"), msg, hashlib.sha256).digest()
    return f"{header_b64}.{body_b64}.{_b64url(sig)}"


def verify_token(token: str):
    """返回 payload dict；无效/过期返回 None"""
    try:
        header_b64, body_b64, sig_b64 = token.split(".")
        msg = f"{header_b64}.{body_b64}".encode("utf-8")
        expected = hmac.new(SECRET_KEY.encode("utf-8"), msg, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64url_decode(sig_b64)):
            return None
        body = json.loads(_b64url_decode(body_b64))
        if body.get("exp", 0) < time.time():
            return None
        return body
    except Exception:
        return None


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, hex_digest = stored.split("$", 1)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return hmac.compare_digest(hex_digest, dk.hex())
    except Exception:
        return False
