from app.core.security import create_access_token, hash_password, verify_password, decode_access_token


def test_bcrypt_and_jwt_roundtrip():
    hashed = hash_password("secret-123")
    assert hashed != "secret-123"
    assert verify_password("secret-123", hashed)
    payload = decode_access_token(create_access_token(7, 2))
    assert payload["sub"] == "7"
    assert payload["tv"] == 2

