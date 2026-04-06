"""Unit tests for Fernet token encryption/decryption."""
import pytest
from cryptography.fernet import Fernet
from app.utils import token_crypto


@pytest.fixture(autouse=True)
def valid_fernet_key(monkeypatch):
    """Inject a known-good Fernet key and reset the singleton for every test."""
    key = Fernet.generate_key().decode()
    monkeypatch.setattr(token_crypto.settings, "fernet_key", key)
    token_crypto._fernet = None
    yield
    token_crypto._fernet = None


def test_encrypt_returns_different_value():
    plaintext = "my-oauth-access-token"
    ciphertext = token_crypto.encrypt_token(plaintext)
    assert ciphertext != plaintext


def test_round_trip():
    plaintext = "super-secret-token-abc123"
    encrypted = token_crypto.encrypt_token(plaintext)
    assert token_crypto.decrypt_token(encrypted) == plaintext


def test_round_trip_long_token():
    long_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjEifQ." + "x" * 512
    assert token_crypto.decrypt_token(token_crypto.encrypt_token(long_token)) == long_token


def test_different_plaintexts_give_different_ciphertexts():
    a = token_crypto.encrypt_token("token-a")
    b = token_crypto.encrypt_token("token-b")
    assert a != b


def test_same_plaintext_gives_different_ciphertexts():
    """Fernet uses a random IV so two encryptions of the same value differ."""
    t = "same-token"
    assert token_crypto.encrypt_token(t) != token_crypto.encrypt_token(t)


def test_auto_generates_key_when_not_configured(monkeypatch):
    """When fernet_key is empty, a key is auto-generated and tokens still work."""
    monkeypatch.setattr(token_crypto.settings, "fernet_key", "")
    token_crypto._fernet = None
    plaintext = "test-token"
    assert token_crypto.decrypt_token(token_crypto.encrypt_token(plaintext)) == plaintext


def test_uses_configured_key(monkeypatch):
    """When a key is provided in settings, it's used consistently."""
    key = Fernet.generate_key().decode()
    monkeypatch.setattr(token_crypto.settings, "fernet_key", key)
    token_crypto._fernet = None
    plaintext = "consistent-token"
    encrypted = token_crypto.encrypt_token(plaintext)
    assert token_crypto.decrypt_token(encrypted) == plaintext
