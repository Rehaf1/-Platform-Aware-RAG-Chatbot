"""
System-level security tests for D-019.

Unlike test_security.py (which uses FastAPI's TestClient, running in-process
with no real network), these tests make genuine HTTP requests over the
network to your actual running `docker compose` stack -- proving real
container networking, a real Postgres connection over the Docker network,
and the real CORS configuration are all correctly wired together as
deployed, not just correct in isolation.

REQUIRES: `docker compose up` running first (docker compose ps should show
both `app` and `postgres` as Up).

Run with: python -m pytest tests/test_security_system.py -v
"""

import time
import requests
import pytest
from dotenv import load_dotenv

load_dotenv(".env")

from app.auth.jwt_auth import create_access_token

BASE_URL = "http://127.0.0.1:8000/api/v1"
HEALTH_URL = "http://127.0.0.1:8000/health"


def make_token(platform_id="imtithal", tenant_id="demo_tenant", user_role="admin", user_id="system_test_user"):
    return create_access_token(platform_id=platform_id, tenant_id=tenant_id, user_id=user_id, user_role=user_role)


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module", autouse=True)
def ensure_server_is_running():
    """Fails fast with a clear message if docker compose isn't up, rather
    than every individual test failing with a confusing connection error."""
    try:
        response = requests.get(HEALTH_URL, timeout=3)
        assert response.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.fail(
            "Could not reach the live server at http://127.0.0.1:8000. "
            "Run `docker compose up` in a separate terminal before running system tests."
        )


# ===========================================================================
# Real network authentication
# ===========================================================================

def test_live_health_check():
    response = requests.get(HEALTH_URL)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_live_ready_check_confirms_real_chroma_connection():
    response = requests.get("http://127.0.0.1:8000/ready")
    assert response.status_code == 200


def test_live_missing_token_rejected_over_real_network():
    response = requests.get(f"{BASE_URL}/documents")
    assert response.status_code == 401


def test_live_valid_admin_token_accepted_over_real_network():
    token = make_token()
    response = requests.get(f"{BASE_URL}/documents", headers=auth_header(token))
    assert response.status_code == 200


def test_live_non_admin_rejected_over_real_network():
    token = make_token(user_role="compliance_manager")
    response = requests.get(f"{BASE_URL}/documents", headers=auth_header(token))
    assert response.status_code == 403


# ===========================================================================
# CORS configuration, as actually served
# ===========================================================================

@pytest.mark.parametrize("origin,should_be_allowed", [
    ("http://localhost:5173", True),   # admin frontend
    ("http://localhost:5174", True),   # chat frontend
    ("http://evil-attacker-site.com", False),
])
def test_cors_only_allows_configured_origins(origin, should_be_allowed):
    """
    Confirms the live server's CORS headers genuinely restrict which
    websites are allowed to call this API from a browser -- not just that
    the code LOOKS correct, but that it behaves correctly when actually hit
    with a real Origin header.
    """
    response = requests.options(
        f"{BASE_URL}/documents",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    allowed_origin_header = response.headers.get("access-control-allow-origin")
    if should_be_allowed:
        assert allowed_origin_header == origin
    else:
        assert allowed_origin_header != origin


# ===========================================================================
# Basic resilience -- a light burst of concurrent requests
# ===========================================================================

def test_server_survives_a_burst_of_concurrent_requests():
    """
    Not a real load test -- just confirms a handful of near-simultaneous
    requests don't crash the server or corrupt shared state (e.g. the
    module-level Chroma collection object).
    """
    import concurrent.futures

    token = make_token()

    def make_request():
        return requests.get(f"{BASE_URL}/documents", headers=auth_header(token), timeout=10)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        responses = [f.result() for f in futures]

    assert all(r.status_code == 200 for r in responses)

    # Confirm the server is still healthy immediately afterward
    health = requests.get(HEALTH_URL)
    assert health.status_code == 200
