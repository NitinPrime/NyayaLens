"""SQLAlchemy database models."""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, String, Text, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.db.types import json_column, str_enum_column
from nyayalens_schemas.enums import (
    AnalysisStatus,
    EvidenceType,
    FactType,
    Jurisdiction,
    LegalSourceType,
    PartyRole,
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CaseRecord(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    case_type: Mapped[Optional[str]] = mapped_column(String(200))
    incident_date: Mapped[Optional[date]] = mapped_column(Date)
    location: Mapped[Optional[str]] = mapped_column(String(500))
    jurisdiction: Mapped[Jurisdiction] = str_enum_column(Jurisdiction, "jurisdiction_enum", Jurisdiction.INDIA)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    amount: Mapped[Optional[str]] = mapped_column(String(100))
    structured_data: Mapped[dict] = json_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    parties: Mapped[list["PartyRecord"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    facts: Mapped[list["FactRecord"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    evidence_items: Mapped[list["EvidenceRecord"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    analyses: Mapped[list["AnalysisRecord"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    messages: Mapped[list["CaseMessage"]] = relationship(back_populates="case", cascade="all, delete-orphan")


class PartyRecord(Base):
    __tablename__ = "parties"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    role: Mapped[PartyRole] = str_enum_column(PartyRole, "party_role_enum", PartyRole.UNKNOWN)
    description: Mapped[Optional[str]] = mapped_column(Text)

    case: Mapped["CaseRecord"] = relationship(back_populates="parties")


class FactRecord(Base):
    __tablename__ = "facts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    fact_type: Mapped[FactType] = str_enum_column(FactType, "fact_type_enum", FactType.ALLEGED)
    fact_date: Mapped[Optional[date]] = mapped_column(Date)
    location: Mapped[Optional[str]] = mapped_column(String(500))
    amount: Mapped[Optional[str]] = mapped_column(String(100))
    confidence: Mapped[str] = mapped_column(String(50), default="medium")
    confidence_rationale: Mapped[Optional[str]] = mapped_column(Text)
    source_evidence_ids: Mapped[list] = json_column(list)

    case: Mapped["CaseRecord"] = relationship(back_populates="facts")


class EvidenceRecord(Base):
    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    evidence_type: Mapped[EvidenceType] = str_enum_column(EvidenceType, "evidence_type_enum")
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text)
    doc_metadata: Mapped[dict] = json_column()
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    case: Mapped["CaseRecord"] = relationship(back_populates="evidence_items")


class LegalSourceRecord(Base):
    __tablename__ = "legal_sources"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_type: Mapped[LegalSourceType] = str_enum_column(LegalSourceType, "legal_source_type_enum")
    jurisdiction: Mapped[Jurisdiction] = str_enum_column(
        Jurisdiction, "legal_jurisdiction_enum", Jurisdiction.INDIA
    )
    section: Mapped[Optional[str]] = mapped_column(String(200))
    article: Mapped[Optional[str]] = mapped_column(String(200))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    effective_date: Mapped[Optional[date]] = mapped_column(Date)
    repeal_date: Mapped[Optional[date]] = mapped_column(Date)
    source_url: Mapped[Optional[str]] = mapped_column(String(2000))
    version: Mapped[Optional[str]] = mapped_column(String(100))
    amendment_history: Mapped[list] = json_column(list)
    embedding: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AnalysisRecord(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    status: Mapped[AnalysisStatus] = str_enum_column(
        AnalysisStatus, "analysis_status_enum", AnalysisStatus.PENDING
    )
    result: Mapped[dict] = json_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    case: Mapped["CaseRecord"] = relationship(back_populates="analyses")


class CaseMessage(Base):
    __tablename__ = "case_messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list] = json_column(list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    case: Mapped["CaseRecord"] = relationship(back_populates="messages")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("analyses.id"), nullable=False)
    stage: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="completed")
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    retrieval_count: Mapped[int] = mapped_column(Integer, default=0)
    model_used: Mapped[Optional[str]] = mapped_column(String(200))
    error: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LegalChunk(Base):
    __tablename__ = "legal_chunks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("legal_sources.id"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    embedding: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100))
    details: Mapped[dict] = json_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
