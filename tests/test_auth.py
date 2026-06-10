from app.auth import hash_password, verify_password, create_access_token, decode_access_token


def test_hash_and_verify_password():
    hashed = hash_password("mysecret")
    assert verify_password("mysecret", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_token():
    token = create_access_token({"sub": "alice", "role": "viewer"})
    payload = decode_access_token(token)
    assert payload["sub"] == "alice"
    assert payload["role"] == "viewer"


def test_decode_invalid_token():
    result = decode_access_token("invalid.token.here")
    assert result is None
