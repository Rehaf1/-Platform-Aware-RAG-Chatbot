import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.database import Base


# ---------------------------------------------------------------------------
# Group 1: Identity and access control
# ---------------------------------------------------------------------------

class Platform(Base):
    __tablename__ = "platforms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform_id = Column(String, unique=True, nullable=False)  # e.g. "imtithal"
    display_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class PlatformConfig(Base):
    """Per-platform configuration: system prompt, allowed modules, fallback messages, etc."""
    __tablename__ = "platform_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform_id = Column(UUID(as_uuid=True), ForeignKey("platforms.id"), nullable=False, unique=True)
    assistant_name = Column(String, nullable=True)
    default_language = Column(String, default="en")
    system_prompt_override = Column(Text, nullable=True)
    fallback_message_en = Column(Text, nullable=True)
    fallback_message_ar = Column(Text, nullable=True)
    allowed_modules = Column(JSONB, nullable=True)  # list of strings, e.g. ["compliance", "audit"]

    platform = relationship("Platform")


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False)  # e.g. "demo_tenant"
    platform_id = Column(UUID(as_uuid=True), ForeignKey("platforms.id"), nullable=False)
    display_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    platform = relationship("Platform")


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)  # e.g. "compliance_manager", "admin"
    description = Column(String, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_user_id = Column(String, nullable=False)  # the "user_id" claim from the JWT
    platform_id = Column(UUID(as_uuid=True), ForeignKey("platforms.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    email = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    platform = relationship("Platform")
    tenant = relationship("Tenant")
    role = relationship("Role")


# ---------------------------------------------------------------------------
# Group 2: Conversations
# ---------------------------------------------------------------------------

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    platform_id = Column(UUID(as_uuid=True), ForeignKey("platforms.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    platform = relationship("Platform")
    tenant = relationship("Tenant")


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    grounded = Column(Boolean, nullable=True)  # only meaningful for assistant messages
    fallback_used = Column(Boolean, nullable=True)
    retrieval_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation")


class Citation(Base):
    __tablename__ = "citations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    document_name = Column(String, nullable=False)
    document_version = Column(String, nullable=True)
    section = Column(String, nullable=True)
    page = Column(String, nullable=True)
    excerpt = Column(Text, nullable=True)

    message = relationship("Message")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_helpful = Column(Boolean, nullable=False)  # thumbs up/down
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    message = relationship("Message")
    user = relationship("User")


# ---------------------------------------------------------------------------
# Group 3: Audit logging
# ---------------------------------------------------------------------------

class AuditLog(Base):
    """
    Immutable record of requests and admin actions. Mirrors
    app/api/audit_log.py's log_chat_request(), but persisted here instead
    of only printed to stdout. Deliberately does NOT store question/answer
    text — see audit_log.py's docstring for why (avoid storing sensitive
    content in a general-purpose log).
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event = Column(String, nullable=False)  # e.g. "chat_request", "document_upload"
    platform_id = Column(String, nullable=True)
    tenant_id = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    user_role = Column(String, nullable=True)
    grounded = Column(Boolean, nullable=True)
    fallback_used = Column(Boolean, nullable=True)
    num_citations = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Group 4: Documents (primarily Person A / Write Path's responsibility)
# ---------------------------------------------------------------------------

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_name = Column(String, nullable=False)
    platform_id = Column(UUID(as_uuid=True), ForeignKey("platforms.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    module = Column(String, nullable=True)
    language = Column(String, nullable=True)
    access_level = Column(String, nullable=True)
    status = Column(String, default="processing")  # processing | indexed | failed
    created_at = Column(DateTime, default=datetime.utcnow)

    platform = relationship("Platform")
    tenant = relationship("Tenant")


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    version = Column(String, nullable=False)
    source_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document")


class DocumentChunk(Base):
    """
    Metadata record referencing a chunk stored in the vector database
    (Chroma). The actual embedding lives in Chroma, not here — this row
    just lets relational queries (e.g. "list all chunks for document X")
    happen without touching the vector store.
    """
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_version_id = Column(UUID(as_uuid=True), ForeignKey("document_versions.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    section = Column(String, nullable=True)
    vector_id = Column(String, nullable=True)  # the corresponding ID in Chroma

    document_version = relationship("DocumentVersion")


# ---------------------------------------------------------------------------
# Group 5: Evaluation
# ---------------------------------------------------------------------------

class EvaluationQuestion(Base):
    __tablename__ = "evaluation_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform_id = Column(UUID(as_uuid=True), ForeignKey("platforms.id"), nullable=False)
    question = Column(Text, nullable=False)
    language = Column(String, default="en")
    expected_behavior = Column(String, nullable=True)  # e.g. "should_answer" | "should_fallback"
    expected_document = Column(String, nullable=True)

    platform = relationship("Platform")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_question_id = Column(UUID(as_uuid=True), ForeignKey("evaluation_questions.id"), nullable=False)
    passed = Column(Boolean, nullable=False)
    actual_answer = Column(Text, nullable=True)
    retrieval_score = Column(Float, nullable=True)
    run_at = Column(DateTime, default=datetime.utcnow)

    evaluation_question = relationship("EvaluationQuestion")