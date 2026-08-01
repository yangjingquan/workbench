import base64
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"

# 登录密码使用进程内 RSA 密钥对加密传输；私钥不会通过接口返回。
_login_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_login_public_key = _login_private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
).decode("ascii")


def login_public_key() -> str:
    return _login_public_key


def decrypt_login_password(ciphertext: str) -> str:
    try:
        encrypted = base64.b64decode(ciphertext, validate=True)
        password = _login_private_key.decrypt(
            encrypted,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        )
        return password.decode("utf-8")
    except (ValueError, TypeError, UnicodeDecodeError) as exc:
        raise ValueError("invalid encrypted password") from exc


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(user_id: int, token_version: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": str(user_id), "tv": token_version, "exp": expires}, settings.jwt_secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
