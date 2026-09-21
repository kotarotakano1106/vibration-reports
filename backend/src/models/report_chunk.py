import uuid
from datetime import date, datetime
from typing import Any

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.db.base import Base

# 仮の次元数。
# Azure OpenAIのEmbeddingモデル確定後、実際の次元数と一致させる。
EMBEDDING_DIMENSIONS = 1536


class ReportChunk(Base):
    """報告書のRAG検索用チャンクとEmbeddingを管理するモデル。"""

    __tablename__ = "report_chunks"

    __table_args__ = (
        UniqueConstraint(
            "report_id",
            "chunk_index",
            name="uq_report_chunks_report_id_chunk_index",
        ),
        CheckConstraint(
            "chunk_index >= 0",
            name="chunk_index_non_negative",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "reports.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    chunk_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="full_report",
        server_default="full_report",
        index=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    embedding: Mapped[list[float]] = mapped_column(
        VECTOR(EMBEDDING_DIMENSIONS),
        nullable=False,
    )

    embedding_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    embedding_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    equipment_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    measurement_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )