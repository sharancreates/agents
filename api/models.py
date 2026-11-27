import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from api.database import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    tier = Column(String, default="free")  # 'free', 'pro', 'enterprise'
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    workspaces = relationship("Workspace", back_populates="organization", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="organization", cascade="all, delete-orphan")
    webhooks = relationship("WebhookEndpoint", back_populates="organization", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="organization")
    credit = relationship("OrganizationCredit", back_populates="organization", uselist=False, cascade="all, delete-orphan")
    payment_orders = relationship("PaymentOrder", back_populates="organization", cascade="all, delete-orphan")
    usage_events = relationship("UsageEvent", back_populates="organization", cascade="all, delete-orphan")

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, index=True, nullable=False)
    challenge_prompt = Column(String, nullable=True)
    default_rubric_weights = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    organization = relationship("Organization", back_populates="workspaces")
    submissions = relationship("Submission", back_populates="workspace")

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, default="Default API Key")
    key_prefix = Column(String(32), index=True, nullable=False)  # e.g. "ak_live_a1b2c3d4"
    key_hash = Column(String(64), unique=True, index=True, nullable=False)  # SHA-256 hex digest
    scopes = Column(JSON, default=lambda: ["eval:read", "eval:write"])
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    organization = relationship("Organization", back_populates="api_keys")

class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String, nullable=False)
    secret_hash = Column(String(64), nullable=False)
    signing_secret_encrypted = Column(String, nullable=True)
    events = Column(JSON, default=lambda: ["evaluation.completed", "evaluation.failed"])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    organization = relationship("Organization", back_populates="webhooks")

    @property
    def signing_secret(self) -> Optional[str]:
        if not self.signing_secret_encrypted:
            return None
        from api.webhook_service import decrypt_webhook_secret
        return decrypt_webhook_secret(self.signing_secret_encrypted)

    @signing_secret.setter
    def signing_secret(self, val: Optional[str]):
        if val is None:
            self.signing_secret_encrypted = None
        else:
            from api.webhook_service import encrypt_webhook_secret
            self.signing_secret_encrypted = encrypt_webhook_secret(val)

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(String, unique=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)

    team_name = Column(String, index=True, nullable=True)
    repo_url = Column(String, index=True)
    commit_sha = Column(String, nullable=True)
    pipeline_status = Column(String, default="pending")  # 'pending', 'running', 'complete', 'failed'
    
    pipeline_started_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    pipeline_completed_at = Column(DateTime, nullable=True)
    
    overall_score = Column(Float, nullable=True)
    synthesis_summary = Column(String, nullable=True)
    
    requires_manual_review = Column(Boolean, default=False)
    review_status = Column(String, default="unreviewed")  # 'unreviewed', 'in_review', 'approved', 'rejected'
    reviewed_by = Column(String, nullable=True)
    
    # Store dimensions as JSON fields conforming to schema
    code_quality = Column(JSON, nullable=True)
    functionality = Column(JSON, nullable=True)
    originality = Column(JSON, nullable=True)
    innovation = Column(JSON, nullable=True)
    
    # Store custom weight configurations used at calculation time
    rubric_weights = Column(JSON, nullable=True)

    # Store participant-facing feedback generated by Feedback Agent
    participant_feedback = Column(JSON, nullable=True)

    # Optional webhook callback URL and audit traces
    webhook_url = Column(String, nullable=True)
    agent_traces = Column(JSON, nullable=True)

    organization = relationship("Organization", back_populates="submissions")
    workspace = relationship("Workspace", back_populates="submissions")

class OrganizationCredit(Base):
    __tablename__ = "organization_credits"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    balance = Column(Float, default=25.0, nullable=False)
    total_purchased = Column(Float, default=0.0, nullable=False)
    total_consumed = Column(Float, default=0.0, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    organization = relationship("Organization", back_populates="credit")

class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    package_id = Column(String, nullable=False)
    razorpay_order_id = Column(String, unique=True, index=True, nullable=False)
    razorpay_payment_id = Column(String, unique=True, index=True, nullable=True)
    amount_paise = Column(Integer, nullable=False)
    currency = Column(String, default="INR", nullable=False)
    credits_to_grant = Column(Integer, nullable=False)
    status = Column(String, default="created", nullable=False)  # 'created', 'paid', 'failed'
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    paid_at = Column(DateTime, nullable=True)

    organization = relationship("Organization", back_populates="payment_orders")

class UsageEvent(Base):
    __tablename__ = "usage_events"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_id = Column(String, index=True, nullable=True)
    credits_deducted = Column(Float, default=1.0, nullable=False)
    balance_after = Column(Float, nullable=True)
    reason = Column(String, default="submission_evaluation", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    organization = relationship("Organization", back_populates="usage_events")

class CodeEmbedding(Base):
    __tablename__ = "code_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(String, index=True, nullable=False)
    file_path = Column(String, index=True, nullable=False)
    symbol_name = Column(String, nullable=True)
    symbol_type = Column(String, default="block", nullable=False)  # 'function', 'class', 'route', 'block'
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding_json = Column(JSON, nullable=False)  # 384-dimensional dense vector as JSON list
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class RubricRequirement(Base):
    __tablename__ = "rubric_requirements"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    track_name = Column(String, index=True, nullable=False)
    requirement_text = Column(String, nullable=False)
    mandatory_keywords = Column(JSON, default=lambda: [])
    min_similarity_threshold = Column(Float, default=0.60, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))


