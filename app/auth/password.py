"""
Password hashing for real user accounts (email + password login), as
distinct from the JWT layer (jwt_auth.py) which handles *tokens* once
someone is already authenticated. This module is the piece that verifies
"is this actually the right password" before a token ever gets issued.

Uses bcrypt directly rather than passlib -- one fewer dependency, and
bcrypt's own API is small enough not to need a wrapper library.
"""

import bcrypt


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # Malformed/legacy hash (e.g. a NULL password_hash for an
        # account that was never given a real password) -- treat as a
        # failed login, never as a crash.
        return False
