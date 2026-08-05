import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv

load_dotenv(".env")

from app.main import app
from app.auth.jwt_auth import create_access_token
from app.retrieval.retriever import retrieve
client = TestClient(app)


def make_token(platform_id, tenant_id, user_role="admin", user_id="test_user"):
    return create_access_token(
        platform_id=platform_id,
        tenant_id=tenant_id,
        user_id=user_id,
        user_role=user_role,
    )


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ---------- TC-10: wrong tenant should never see another tenant's data ----------

def test_cross_tenant_isolation_on_chat():
    """A user from tenant_a should never get answers grounded in tenant_b's documents."""
    token_tenant_b = make_token(platform_id="imtithal", tenant_id="tenant_b", user_role="compliance_manager")

    response = client.post(
        "/api/v1/chat",
        headers=auth_header(token_tenant_b),
        json={"question": "How do I assign a control owner?", "language": "en"},
    )
    assert response.status_code == 200
    body = response.json()
    # tenant_b has no documents ingested — must fall back, never fabricate or leak tenant_a's answer
    assert body["fallback_used"] is True
    assert body["grounded"] is False


# ---------- TC-03: cross-platform isolation ----------

def test_cross_platform_isolation_on_chat():
    """An EMDAD-scoped question asked while platform_id=imtithal must not leak IMTITHAL content
    and must not return an EMDAD answer that doesn't exist in IMTITHAL's knowledge base."""
    token = make_token(platform_id="imtithal", tenant_id="demo_tenant", user_role="compliance_manager")

    response = client.post(
        "/api/v1/chat",
        headers=auth_header(token),
        json={"question": "How do I create a new supplier?", "language": "en"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["fallback_used"] is True


# ---------- TC-11 / admin authorization: non-admin cannot upload ----------

def test_non_admin_cannot_upload_document():
    token = make_token(platform_id="imtithal", tenant_id="demo_tenant", user_role="compliance_manager")

    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_header(token),
        files={"file": ("test.txt", b"some content", "text/plain")},
    )
    assert response.status_code == 403


def test_admin_can_upload_document():
    token = make_token(platform_id="imtithal", tenant_id="demo_tenant", user_role="admin")

    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_header(token),
        files={"file": ("isolation_test_doc.txt", b"Test content for isolation suite.", "text/plain")},
    )
    assert response.status_code in (200, 409)  # 409 if already uploaded by a prior test run


# ---------- No token at all ----------

def test_missing_token_rejected_on_upload():
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", b"content", "text/plain")},
    )
    assert response.status_code == 401


def test_missing_token_rejected_on_chat():
    response = client.post(
        "/api/v1/chat",
        json={"question": "test", "language": "en"},
    )
    assert response.status_code == 401


# ---------- Admin actions scoped to their own platform only ----------

def test_admin_cannot_delete_document_outside_their_platform():
    """An imtithal admin's delete request should never affect emdad's documents,
    even if they somehow guess a document name that exists there."""
    imtithal_admin_token = make_token(platform_id="imtithal", tenant_id="demo_tenant", user_role="admin")

    # Upload something under emdad first, using an emdad-scoped token
    emdad_admin_token = make_token(platform_id="emdad", tenant_id="demo_tenant", user_role="admin")
    client.post(
        "/api/v1/documents/upload",
        headers=auth_header(emdad_admin_token),
        files={"file": ("shared_name_test.txt", b"EMDAD-only content.", "text/plain")},
    )

    # imtithal admin tries to delete a document with the same name
    response = client.delete(
        "/api/v1/documents/shared_name_test.txt",
        headers=auth_header(imtithal_admin_token),
    )
    assert response.status_code == 200  # the call succeeds...

    # ...but EMDAD's copy must still exist, since the delete was scoped to imtithal only
    from app.retrieval.vector_store import collection
    results = collection.get(where={"$and": [{"platform_id": "emdad"}, {"document_name": "shared_name_test.txt"}]})
    assert len(results["ids"]) > 0, "Cross-platform delete leaked! EMDAD's document was deleted by an IMTITHAL admin."
    



# ---------- Cross-tenant isolation at the retrieval layer itself ----------

def test_retrieval_never_returns_another_tenants_chunks():
    """Upload a document under a brand-new tenant, then confirm a different
    tenant's retrieve() call never sees it, even with an identical question."""
    admin_token = make_token(platform_id="imtithal", tenant_id="tenant_isolation_test", user_role="admin")

    client.post(
        "/api/v1/documents/upload",
        headers=auth_header(admin_token),
        files={"file": ("tenant_isolation_doc.txt", b"Secret content only tenant_isolation_test should see.", "text/plain")},
    )

    # A different tenant asks a question that would semantically match this content
    result = retrieve(
        "secret content",
        platform_id="imtithal",
        tenant_id="demo_tenant",  # NOT the tenant that owns this document
    )

    leaked = [c for c in result.chunks if c.tenant_id == "tenant_isolation_test"]
    assert leaked == [], "Cross-tenant leak! demo_tenant's retrieval returned another tenant's chunk."


# ---------- Role-based content filtering at the retrieval layer ----------

def test_role_restricted_content_excluded_for_wrong_role():
    """A chunk tagged with roles=admin should not be retrievable by a
    compliance_manager, but should be retrievable by an admin."""
    admin_token = make_token(platform_id="imtithal", tenant_id="demo_tenant", user_role="admin")

    client.post(
        "/api/v1/documents/upload",
        headers=auth_header(admin_token),
        data={"roles": "admin"},
        files={"file": ("admin_only_doc.txt", b"Extremely confidential admin-only procedure text.", "text/plain")},
    )

    # Wrong role — should NOT see this chunk
    result_wrong_role = retrieve(
        "confidential admin-only procedure",
        platform_id="imtithal",
        tenant_id="demo_tenant",
        user_role="compliance_manager",
    )
    leaked = [c for c in result_wrong_role.chunks if "admin_only_doc" in c.document_name]
    assert leaked == [], "Role leak! compliance_manager retrieved an admin-only chunk."

    # Correct role — SHOULD see this chunk
    result_right_role = retrieve(
        "confidential admin-only procedure",
        platform_id="imtithal",
        tenant_id="demo_tenant",
        user_role="admin",
    )
    found = [c for c in result_right_role.chunks if "admin_only_doc" in c.document_name]
    assert found != [], "Admin should be able to retrieve admin-only content, but got nothing."