import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import Settings, get_settings
from app.core.install import is_installed, load_install_config

TOKEN_ALGORITHM = hashlib.sha256
PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 390000
API_TOKEN_PREFIX = "mtx_"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return "$".join(
        [
            PASSWORD_ALGORITHM,
            str(PASSWORD_ITERATIONS),
            _b64encode(salt),
            _b64encode(digest),
        ]
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt, digest = password_hash.split("$", 3)
    except ValueError:
        return False
    if algorithm != PASSWORD_ALGORITHM:
        return False
    expected = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), _b64decode(salt), int(iterations))
    return hmac.compare_digest(_b64encode(expected), digest)


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.token_expire_minutes)
    payload = {"sub": subject, "exp": int(expires_at.timestamp())}
    payload_part = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign(payload_part, settings)
    return f"{payload_part}.{signature}"


def decode_access_token(token: str) -> str | None:
    try:
        payload_part, signature = token.split(".", 1)
    except ValueError:
        return None
    expected = _sign(payload_part, get_settings())
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        payload = json.loads(_b64decode(payload_part))
    except (ValueError, json.JSONDecodeError):
        return None
    if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
        return None
    subject = str(payload.get("sub") or "")
    return subject if subject.isdigit() else None


def create_api_token() -> str:
    return f"{API_TOKEN_PREFIX}{secrets.token_urlsafe(32)}"


def hash_api_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def encrypt_secret(plain: str) -> str:
    return _fernet().encrypt(plain.encode("utf-8")).decode("ascii")


def decrypt_secret(encrypted: str) -> str:
    try:
        return _fernet().decrypt(encrypted.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        raise ValueError("Invalid encrypted secret") from exc


def _fernet() -> Fernet:
    digest = hashlib.sha256(_secret_key(get_settings()).encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _secret_key(settings: Settings) -> str:
    if is_installed():
        return load_install_config().secret_key
    return f"{settings.app_slug}-installing"


def _sign(payload_part: str, settings: Settings) -> str:
    digest = hmac.new(_secret_key(settings).encode("utf-8"), payload_part.encode("utf-8"), TOKEN_ALGORITHM).digest()
    return _b64encode(digest)


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)
