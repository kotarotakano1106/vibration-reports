"""RAGチャットAPIで使用するリクエスト・レスポンスSchema。"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.src.workflows.states.chat_state import (
    DEFAULT_CHAT_CHUNK_TYPES,
)


class RagChatRequest(BaseModel):
    """過去レポートを根拠に回答するチャットリクエスト。"""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="利用者の質問",
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="参照する検索結果の最大件数",
    )
    equipment_id: str | None = Field(
        default=None,
        max_length=100,
        description="設備IDによる絞り込み",
    )
    measurement_date_from: date | None = Field(
        default=None,
        description="検索開始日",
    )
    measurement_date_to: date | None = Field(
        default=None,
        description="検索終了日",
    )
    chunk_types: list[str] = Field(
        default_factory=lambda: list(
            DEFAULT_CHAT_CHUNK_TYPES
        ),
        min_length=1,
        description="検索対象のチャンク種別",
    )

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        """質問文の前後空白を除去する。"""

        normalized = value.strip()
        if not normalized:
            raise ValueError(
                "queryを空にできません。"
            )
        return normalized

    @field_validator("equipment_id")
    @classmethod
    def normalize_equipment_id(
        cls,
        value: str | None,
    ) -> str | None:
        """設備IDの前後空白を除去する。"""

        if value is None:
            return None

        normalized = value.strip()
        return normalized or None

    @field_validator("chunk_types")
    @classmethod
    def normalize_chunk_types(
        cls,
        value: list[str],
    ) -> list[str]:
        """チャンク種別を正規化して重複を除去する。"""

        normalized: list[str] = []

        for chunk_type in value:
            item = chunk_type.strip()
            if item and item not in normalized:
                normalized.append(item)

        if not normalized:
            raise ValueError(
                "chunk_typesを空にできません。"
            )

        return normalized

    @model_validator(mode="after")
    def validate_date_range(self):
        """検索期間の前後関係を確認する。"""

        if (
            self.measurement_date_from is not None
            and self.measurement_date_to is not None
            and self.measurement_date_from
            > self.measurement_date_to
        ):
            raise ValueError(
                "検索開始日は検索終了日以前にしてください。"
            )

        return self


class RagChatSourceResponse(BaseModel):
    """RAGチャット回答の参照元1件。"""

    report_chunk_id: UUID
    report_id: UUID
    chunk_type: str
    equipment_id: str
    measurement_date: date | None
    similarity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )


class RagChatResponse(BaseModel):
    """RAGチャットAPIのレスポンス。"""

    query: str
    answer: str
    source_count: int
    sources: list[RagChatSourceResponse]
