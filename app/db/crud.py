from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from app.db.models import (
    Platform,
    Tenant,
    Role,
    User,
    Conversation,
    Message,
    Citation,
    AuditLog,
    Document,
    DocumentVersion,
    DocumentChunk,
)


# ---------------------------------------------------------------------------
# Identity rows: JWT carries short strings (platform_id="imtithal"), the
# database uses UUIDs. These functions translate one to the other,
# creating the row on first sight rather than requiring pre-seeding.
# ---------------------------------------------------------------------------

def get_or_create_platform(db: Session, platform_id: str) -> Platform:
    platform = db.query(Platform).filter(Platform.platform_id == platform_id).first()
    if platform is None:
        platform = Platform(platform_id=platform_id, display_name=platform_id.upper())
        db.add(platform)
        db.commit()
        db.refresh(platform)
    return platform


def get_or_create_tenant(db: Session, platform: Platform, tenant_id: str) -> Tenant:
    tenant = (
        db.query(Tenant)
        .filter(Tenant.tenant_id == tenant_id, Tenant.platform_id == platform.id)
        .first()
    )
    if tenant is None:
        tenant = Tenant(tenant_id=tenant_id, platform_id=platform.id, display_name=tenant_id)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    return tenant


def get_or_create_role(db: Session, role_name: Optional[str]) -> Optional[Role]:
    if not role_name:
        return None
    role = db.query(Role).filter(Role.name == role_name).first()
    if role is None:
        role = Role(name=role_name)
        db.add(role)
        db.commit()
        db.refresh(role)
    return role


def get_or_create_user(
    db: Session,
    platform: Platform,
    tenant: Tenant,
    external_user_id: str,
    role_name: Optional[str],
) -> User:
    user = (
        db.query(User)
        .filter(
            User.external_user_id == external_user_id,
            User.platform_id == platform.id,
            User.tenant_id == tenant.id,
        )
        .first()
    )
    role = get_or_create_role(db, role_name)

    if user is None:
        user = User(
            external_user_id=external_user_id,
            platform_id=platform.id,
            tenant_id=tenant.id,
            role_id=role.id if role else None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif role and user.role_id != role.id:
        # role may have changed since we last saw this user (e.g. promoted)
        user.role_id = role.id
        db.commit()
        db.refresh(user)

    return user


# ---------------------------------------------------------------------------
# Conversation / message / citation persistence
# ---------------------------------------------------------------------------

def create_conversation(
    db: Session, user: User, platform: Platform, tenant: Tenant, title: Optional[str] = None
) -> Conversation:
    conversation = Conversation(
        user_id=user.id,
        platform_id=platform.id,
        tenant_id=tenant.id,
        title=title,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def add_message(
    db: Session,
    conversation: Conversation,
    *,
    role: str,
    content: str,
    grounded: Optional[bool] = None,
    fallback_used: Optional[bool] = None,
    retrieval_score: Optional[float] = None,
) -> Message:
    message = Message(
        conversation_id=conversation.id,
        role=role,
        content=content,
        grounded=grounded,
        fallback_used=fallback_used,
        retrieval_score=retrieval_score,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message



def add_citations(db: Session, message: Message, citations: List[Dict[str, Any]]) -> None:
    for c in citations:
        db.add(
            Citation(
                message_id=message.id,
                document_name=c.get("document_name", ""),
                document_version=c.get("document_version"),
                section=c.get("section"),
                page=c.get("page"),
                excerpt=c.get("excerpt"),
            )
        )
    db.commit()


# ---------------------------------------------------------------------------
# get_or_create_document / document_versions / document_chunks
# ---------------------------------------------------------------------------

def get_or_create_document(
    db: Session,
    platform: Platform,
    tenant: Tenant,
    document_name: str,
    module: Optional[str] = None,
    language: Optional[str] = None,
    access_level: Optional[str] = None,
) -> Document:
    document = (
        db.query(Document)
        .filter(
            Document.document_name == document_name,
            Document.platform_id == platform.id,
            Document.tenant_id == tenant.id,
        )
        .first()
    )
    if document is None:
        document = Document(
            document_name=document_name,
            platform_id=platform.id,
            tenant_id=tenant.id,
            module=module,
            language=language,
            access_level=access_level,
        )
        db.add(document)
        db.commit()
        db.refresh(document)
    return document
    


def create_document_version(
    db: Session,
    document: Document,
    version: str,
    source_path: Optional[str] = None,
) -> DocumentVersion:
    document_version = DocumentVersion(
        document_id=document.id,
        version=version,
        source_path=source_path,
    )

    db.add(document_version)
    db.commit()
    db.refresh(document_version)

    return document_version


def create_document_chunks(
    db: Session,
    document_version: DocumentVersion,
    chunks: List[Dict[str, Any]],  # each dict: {"chunk_index": int, "section": str, "vector_id": str}
) -> List[DocumentChunk]:
    chunk_rows = []
    for chunk in chunks:
        chunk_row = DocumentChunk(
            document_version_id=document_version.id,
            chunk_index=chunk["chunk_index"],
            section=chunk.get("section"),
            vector_id=chunk["vector_id"],
        )
        db.add(chunk_row)
        chunk_rows.append(chunk_row)

    db.commit()
    for chunk_row in chunk_rows:
        db.refresh(chunk_row)

    return chunk_rows
# ---------------------------------------------------------------------------
# Audit log persistence — mirrors app/api/audit_log.py's fields, but saved
# to the database instead of (or in addition to) stdout.
# ---------------------------------------------------------------------------

def log_audit_event(
    db: Session,
    *,
    event: str,
    platform_id: Optional[str],
    tenant_id: Optional[str],
    user_id: Optional[str],
    user_role: Optional[str],
    grounded: Optional[bool] = None,
    fallback_used: Optional[bool] = None,
    num_citations: Optional[int] = None,
    latency_ms: Optional[float] = None,
) -> None:
    db.add(
        AuditLog(
            event=event,
            platform_id=platform_id,
            tenant_id=tenant_id,
            user_id=user_id,
            user_role=user_role,
            grounded=grounded,
            fallback_used=fallback_used,
            num_citations=num_citations,
            latency_ms=latency_ms,
        )
    )
    db.commit()