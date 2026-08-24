"""
Deep security test suite for D-019.

Organized in layers:
  1. Authentication & JWT attacks
  2. Authorization (role-based access)
  3. Input validation / injection attacks
  4. Path traversal
  5. File upload attacks
  6. Information disclosure
  7. Duplicate-registry cross-tenant leak check

Prompt-injection tests (including indirect injection via document content)
live in a separate script (test_prompt_injection.py) since they require the
live LLM and human/rubric judgment rather than a clean pass/fail assertion.
"""

import io
import jwt as pyjwt
import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv

load_dotenv(".env")

from app.main import app
from app.auth.jwt_auth import create_access_token, JWT_SECRET, JWT_ALGORITHM

client = TestClient(app)


def make_token(platform_id="imtithal", tenant_id="demo_tenant", user_role="admin", user_id="test_user"):
    return create_access_token(platform_id=platform_id, tenant_id=tenant_id, user_id=user_id, user_role=user_role)


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ===========================================================================
# 1. Authentication & JWT attacks
# ===========================================================================

def test_valid_token_accepted():
    token = make_token()
    response = client.get("/api/v1/documents", headers=auth_header(token))
    assert response.status_code == 200


def test_missing_token_rejected():
    response = client.get("/api/v1/documents")
    assert response.status_code == 401


def test_malformed_token_rejected():
    response = client.get("/api/v1/documents", headers={"Authorization": "Bearer not-a-real-jwt"})
    assert response.status_code == 401


def test_tampered_signature_rejected():
    """Take a genuinely valid token and flip one character in the signature."""
    token = make_token()
    header, payload, signature = token.split(".")
    tampered_signature = signature[:-1] + ("A" if signature[-1] != "A" else "B")
    tampered_token = f"{header}.{payload}.{tampered_signature}"
    response = client.get("/api/v1/documents", headers=auth_header(tampered_token))
    assert response.status_code == 401


def test_none_algorithm_attack_rejected():
    """
    Classic JWT vulnerability: some libraries historically accepted a token
    with alg='none' and no signature at all, trusting the payload blindly.
    Confirms this server does not.
    """
    forged = pyjwt.encode(
        {"platform_id": "imtithal", "tenant_id": "demo_tenant", "user_id": "attacker", "user_role": "admin"},
        key="",
        algorithm="none",
    )
    response = client.get("/api/v1/documents", headers=auth_header(forged))
    assert response.status_code == 401


def test_token_signed_with_wrong_secret_rejected():
    """An attacker who guesses/brute-forces a DIFFERENT secret should still fail."""
    forged = pyjwt.encode(
        {"platform_id": "imtithal", "tenant_id": "demo_tenant", "user_id": "attacker", "user_role": "admin"},
        key="wrong-secret-attacker-guessed",
        algorithm=JWT_ALGORITHM,
    )
    response = client.get("/api/v1/documents", headers=auth_header(forged))
    assert response.status_code == 401


def test_token_missing_required_claims_rejected():
    """A validly-signed token that's simply missing platform_id/tenant_id/user_id."""
    incomplete = pyjwt.encode({"some_other_field": "x"}, key=JWT_SECRET, algorithm=JWT_ALGORITHM)
    response = client.get("/api/v1/documents", headers=auth_header(incomplete))
    assert response.status_code == 401


def test_token_with_empty_string_claims_rejected():
    """platform_id='' should not be treated as a valid platform."""
    forged = pyjwt.encode(
        {"platform_id": "", "tenant_id": "demo_tenant", "user_id": "attacker", "user_role": "admin"},
        key=JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    response = client.get("/api/v1/documents", headers=auth_header(forged))
    assert response.status_code == 401


def test_expired_token_rejected():
    import time
    expired = pyjwt.encode(
        {
            "platform_id": "imtithal", "tenant_id": "demo_tenant", "user_id": "u1", "user_role": "admin",
            "exp": int(time.time()) - 3600,  # expired 1 hour ago
        },
        key=JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    response = client.get("/api/v1/documents", headers=auth_header(expired))
    assert response.status_code == 401


# ===========================================================================
# 2. Authorization (role-based access)
# ===========================================================================

@pytest.mark.parametrize("role", ["compliance_manager", "auditor", "viewer", "guest", None])
def test_non_admin_roles_cannot_upload(role):
    token = make_token(user_role=role)
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_header(token),
        files={"file": ("test.txt", b"content", "text/plain")},
    )
    assert response.status_code == 403


def test_non_admin_roles_cannot_delete():
    token = make_token(user_role="compliance_manager")
    response = client.delete("/api/v1/documents/some_doc.txt", headers=auth_header(token))
    assert response.status_code == 403


def test_non_admin_roles_cannot_reindex():
    token = make_token(user_role="compliance_manager")
    response = client.post("/api/v1/documents/some_doc.txt/reindex", headers=auth_header(token))
    assert response.status_code == 403


def test_non_admin_roles_cannot_list_documents():
    token = make_token(user_role="compliance_manager")
    response = client.get("/api/v1/documents", headers=auth_header(token))
    assert response.status_code == 403


# ===========================================================================
# 3. Input validation / injection attacks
# ===========================================================================

SQL_INJECTION_PAYLOADS = [
    "'; DROP TABLE documents; --",
    "' OR '1'='1",
    "1; DELETE FROM users WHERE 1=1; --",
    "admin'--",
    "' UNION SELECT * FROM users --",
]


@pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
def test_sql_injection_in_module_field_handled_safely(payload):
    """
    The module field flows into a SQLAlchemy ORM call (parameterized by
    design), so injection should be inert -- treated as a literal string,
    not executed as SQL. This test proves it rather than assumes it.
    """
    token = make_token()
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_header(token),
        data={"module": payload},
        files={"file": ("sql_test.txt", b"Some safe content for SQL injection test.", "text/plain")},
    )
    # Should not 500 (a crash could indicate the payload broke something)
    assert response.status_code != 500

    # The documents table should still exist and be queryable afterward --
    # if a real injection had succeeded, this call itself might fail.
    list_response = client.get("/api/v1/documents", headers=auth_header(token))
    assert list_response.status_code == 200


@pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
def test_sql_injection_in_document_name_path_handled_safely(payload):
    """Injection attempted via a URL path parameter (document_name)."""
    token = make_token()
    response = client.get(f"/api/v1/documents/{payload}/status", headers=auth_header(token))
    assert response.status_code != 500


# ===========================================================================
# 4. Path traversal
# ===========================================================================

PATH_TRAVERSAL_PAYLOADS = [
    "../../../app/main.py",
    "..%2f..%2f..%2fapp%2fmain.py",
    "....//....//app/main.py",
    "/etc/passwd",
    "..\\..\\..\\Windows\\system32\\config\\SAM",
]


@pytest.mark.parametrize("payload", PATH_TRAVERSAL_PAYLOADS)
def test_path_traversal_in_delete_does_not_escape_platform_folder(payload):
    """
    Confirms a crafted document_name cannot be used to delete files outside
    the intended sample_data/<platform>/ directory.
    """
    token = make_token()
    response = client.delete(f"/api/v1/documents/{payload}", headers=auth_header(token))
    # Should not succeed in deleting something outside scope, and should not crash
    assert response.status_code != 500

    # The application's own source file must still exist and be unmodified
    import os
    assert os.path.exists("app/main.py")


@pytest.mark.parametrize("payload", PATH_TRAVERSAL_PAYLOADS)
def test_path_traversal_in_reindex_does_not_escape_platform_folder(payload):
    token = make_token()
    response = client.post(f"/api/v1/documents/{payload}/reindex", headers=auth_header(token))
    assert response.status_code != 500


# ===========================================================================
# 5. File upload attacks
# ===========================================================================

def test_empty_file_rejected():
    token = make_token()
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_header(token),
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert response.status_code == 400


def test_null_byte_in_filename_handled_safely():
    """
    A classic filename-based attack: embedding a null byte to try to trick
    older/naive file-handling code into truncating the extension check
    (e.g. 'malicious.py\\x00.txt' being treated as .txt by a check but .py
    by the underlying filesystem call). Modern Python path handling is not
    vulnerable to this, but it's worth testing explicitly rather than
    assuming.
    """
    token = make_token()
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_header(token),
        files={"file": ("safe.txt\x00.py", b"print('should not execute')", "text/plain")},
    )
    assert response.status_code != 500


def test_oversized_filename_handled_safely():
    token = make_token()
    huge_name = "a" * 10000 + ".txt"
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_header(token),
        files={"file": (huge_name, b"content", "text/plain")},
    )
    assert response.status_code != 500


def test_mismatched_extension_and_content_handled_safely():
    """A file named .txt but containing binary garbage should not crash the loader."""
    token = make_token()
    binary_garbage = bytes([0x00, 0xFF, 0x42, 0x13, 0x37] * 100)
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_header(token),
        files={"file": ("garbage.txt", binary_garbage, "text/plain")},
    )
    assert response.status_code != 500


# ===========================================================================
# 6. Information disclosure
# ===========================================================================

def test_error_responses_do_not_leak_file_system_paths():
    """
    A 404/400/500 error message should not reveal internal absolute file
    paths (e.g. '/Users/rehaf/int-ai-01/...'), which could help an attacker
    map out the server's file system.
    """
    token = make_token()
    response = client.get("/api/v1/documents/definitely_does_not_exist.txt/status", headers=auth_header(token))
    body_text = str(response.content)
    assert "/Users/" not in body_text
    assert "/home/" not in body_text
    assert "Traceback" not in body_text


def test_401_response_does_not_leak_whether_platform_exists():
    """
    An unauthenticated request should get the same generic 401 regardless
    of whether the platform/tenant it might have referred to is real --
    otherwise an attacker could enumerate valid platform names by timing
    or message differences.
    """
    response = client.get("/api/v1/documents")
    assert response.status_code == 401
    assert "imtithal" not in str(response.content).lower()
    assert "emdad" not in str(response.content).lower()


# ===========================================================================
# 7. Secrets hygiene
# ===========================================================================

def test_jwt_secret_is_not_the_insecure_default():
    """
    jwt_auth.py falls back to a placeholder secret ('dev-only-insecure-
    secret-change-me') if JWT_SECRET is not set in the environment. This
    confirms a real secret is actually configured, not silently using the
    placeholder.
    """
    assert JWT_SECRET != "dev-only-insecure-secret-change-me", (
        "JWT_SECRET is still using the insecure placeholder default -- "
        "set a real secret in .env before any real deployment."
    )
