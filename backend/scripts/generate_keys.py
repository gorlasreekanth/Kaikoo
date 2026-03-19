"""Run: python scripts/generate_keys.py
Outputs the keys you need to set in your .env file.
"""
import secrets
from cryptography.fernet import Fernet

print("SECRET_KEY=" + secrets.token_hex(32))
print("FERNET_KEY=" + Fernet.generate_key().decode())
