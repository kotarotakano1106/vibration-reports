import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.db.base import Base


class Report(Base):
    __tablename__ = "reports"

    __table_args__ = (
        CheckConstraint(
            "record_count > 0",
            name="record_count_positive",
        ),
        CheckConstraint(
            "anomaly_count >= 0",
            name="anomaly_count_non_negative",
        ),
        CheckConstraint(
            "minimum_value <= maximum_value",
            name="minimum_not_greater_than_maximum",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    uploaded_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "uploaded_files.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        unique=True,
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
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

    weather: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    record_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    minimum_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    maximum_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    average_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    median_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    standard_deviation: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    threshold_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    anomaly_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        index=True,
    )

    anomaly_details: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="requires_attention",
        server_default="requires_attention",
        index=True,
    )

    ai_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    ai_analysis: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    recommendation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    report_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    ai_model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    prompt_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    chart_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    pdf_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    pdf_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )