"""
Unit-level security tests for D-019.

These call individual functions DIRECTLY, with no HTTP layer, no FastAPI
TestClient, and no live server -- the fastest, most isolated layer of the
testing pyramid. If one of these fails, the problem is in one specific
function, not in how components interact.
"""

import time
import jwt as pyjwt
import pytest
from dotenv import load_dotenv

load_dotenv(".env")

from app.auth.jwt_auth import create_access_token, _decode_token, JWT_SECRET, JWT_ALGORITHM, TrustedContext
from app.auth.authorization import require_admin
from app.ingestion.collection_and_validation import validate_document
from app.ingestion.duplicate_detection import hash_text, normalize_for_hashing, is_duplicate
from fastapi import HTTPException


# ===========================================================================
# JWT — encode/decode functions directly
# ===========================================================================

def test_create_and_decode_valid_token():
    token = create_access_token(platform_id="imtithal", tenant_id="demo_tenant", user_id="u1", user_role="admin")
    payload = _decode_token(token)
    assert payload["platform_id"] == "imtithal"
    assert payload["tenant_id"] == "demo_tenant"
    assert payload["user_role"] == "admin"


def test_decode_rejects_tampered_token():
    token = create_access_token(platform_id="imtithal", tenant_id="demo_tenant", user_id="u1")
    header, payload, sig = token.split(".")
    tampered = f"{header}.{payload}.{sig[:-2]}XX"
    with pytest.raises(HTTPException):
        _decode_token(tampered)


def test_decode_rejects_expired_token():
    expired = pyjwt.encode(
        {"platform_id": "imtithal", "tenant_id": "demo_tenant", "user_id": "u1", "exp": int(time.time()) - 10},
        key=JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    with pytest.raises(HTTPException):
        _decode_token(expired)


def test_decode_rejects_wrong_secret():
    forged = pyjwt.encode(
        {"platform_id": "imtithal", "tenant_id": "demo_tenant", "user_id": "attacker"},
        key="wrong-secret",
        algorithm=JWT_ALGORITHM,
    )
    with pytest.raises(HTTPException):
        _decode_token(forged)


# ===========================================================================
# require_admin — called directly with a fake TrustedContext, no HTTP
# ===========================================================================

def test_require_admin_allows_admin_role():
    ctx = TrustedContext(platform_id="imtithal", tenant_id="demo_tenant", user_role="admin", user_id="u1")
    result = require_admin(ctx=ctx)
    assert result is ctx  # should pass through unchanged


@pytest.mark.parametrize("role", ["compliance_manager", "auditor", "viewer", None, "", "Admin", "ADMIN"])
def test_require_admin_rejects_every_non_exact_admin_role(role):
    """
    Deliberately includes near-misses like 'Admin' and 'ADMIN' -- confirms
    the role check is exact-match, not case-insensitive (which could
    otherwise be a real, subtle privilege-escalation bug).
    """
    ctx = TrustedContext(platform_id="imtithal", tenant_id="demo_tenant", user_role=role, user_id="u1")
    with pytest.raises(HTTPException) as exc_info:
        require_admin(ctx=ctx)
    assert exc_info.value.status_code == 403


# ===========================================================================
# validate_document — called directly on real and fake files
# ===========================================================================

def test_validate_document_rejects_nonexistent_file():
    is_valid, reason = validate_document("this_file_genuinely_does_not_exist.txt")
    assert is_valid is False
    assert "not exist" in reason.lower() or "not found" in reason.lower()


def test_validate_document_rejects_empty_file(tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_bytes(b"")
    is_valid, reason = validate_document(str(empty_file))
    assert is_valid is False


def test_validate_document_rejects_unsupported_extension(tmp_path):
    exe_file = tmp_path / "malicious.exe"
    exe_file.write_bytes(b"fake binary content")
    is_valid, reason = validate_document(str(exe_file))
    assert is_valid is False


def test_validate_document_accepts_genuine_small_text_file(tmp_path):
    real_file = tmp_path / "real.txt"
    real_file.write_text("This is genuine, non-empty content.")
    is_valid, reason = validate_document(str(real_file))
    assert is_valid is True


# ===========================================================================
# Duplicate detection — hashing and normalization, called directly
# ===========================================================================

def test_identical_content_produces_identical_hash():
    text_a = "The quick brown fox jumps over the lazy dog."
    text_b = "The quick brown fox jumps over the lazy dog."
    assert hash_text(text_a) == hash_text(text_b)


def test_different_content_produces_different_hash():
    assert hash_text("Content A") != hash_text("Content B")


def test_normalize_makes_whitespace_variants_match():
    """
    A PDF-extracted version with a line-wrap mid-word should hash the same
    as a cleanly-typed version, once normalized -- this is the exact fix
    from earlier bug work, now locked in as a regression test.
    """
    version_a = "The control\nowner is responsible."
    version_b = "The control owner is responsible."
    assert hash_text(normalize_for_hashing(version_a)) == hash_text(normalize_for_hashing(version_b))


def test_is_duplicate_true_only_for_known_hash():
    registry = {"abc123": {"document_name": "existing.txt"}}
    assert is_duplicate("abc123", registry) is True
    assert is_duplicate("not_in_registry", registry) is False
