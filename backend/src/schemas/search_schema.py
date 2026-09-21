"""RAG検索APIで使用するリクエスト・レスポンスSchema。"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

DEFAULT_SEARCH_CHUNK_TYPES = [
    "analysis_summary",
    "judgment_reason",
    "recommendation",
    "anomaly_details",
]


class RagSearchRequest(BaseModel):
    """過去レポートの類似検索リクエスト。"""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="検索文",
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="取得件数",
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
            DEFAULT_SEARCH_CHUNK_TYPES
        ),
        min_length=1,
        description="検索対象のチャンク種別",
    )

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        """検索文の前後空白を除去する。"""

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


class RagSearchResultResponse(BaseModel):
    """過去レポートの類似検索結果1件。"""

    report_chunk_id: UUID
    report_id: UUID
    chunk_index: int
    chunk_type: str
    content: str
    equipment_id: str
    measurement_date: date | None
    distance: float
    similarity: float
    embedding_model: str
    metadata_json: dict[str, object]


class RagSearchResponse(BaseModel):
    """過去レポートの類似検索レスポンス。"""

    query: str
    result_count: int
    results: list[RagSearchResultResponse]
