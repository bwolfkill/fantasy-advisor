import time
from datetime import timedelta

from jwt import ExpiredSignatureError, InvalidSignatureError

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_hash_and_verify_password():
    password = "mysecretpassword"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


def test_wrong_password_does_not_verify():
    password = "mysecretpassword"
    wrong_password = "wrongpassword"
    hashed = hash_password(password)
    assert verify_password(wrong_password, hashed) is False


def test_create_and_decode_token():
    subject = "user123"
    token = create_access_token(subject)
    decoded = decode_access_token(token)
    assert decoded["sub"] == subject


def test_expired_token_raises():
    subject = "user123"
    token = create_access_token(subject, expires_delta=timedelta(seconds=1))
    time.sleep(1)
    try:
        decode_access_token(token)
        raise AssertionError("Expected ExpiredSignatureError to be raised")
    except ExpiredSignatureError:
        pass


def test_tampered_token_raises():
    subject = "user123"
    token = create_access_token(subject)
    tampered_token = token[:-5] + "abcde"
    try:
        decode_access_token(tampered_token)
        raise AssertionError("Expected JWTError to be raised")
    except InvalidSignatureError:
        pass
