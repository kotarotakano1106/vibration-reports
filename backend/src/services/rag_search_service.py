"""過去レポートのベクトル類似検索を管理するService。"""

from dataclasses import dataclass
from datetime import date

from backend.src.repositories.vector_repository import (
    VectorRepository,
)
from backend.src.services.azure_openai_service import (
    AzureOpenAIService,
    AzureOpenAIServiceError,
)

DEFAULT_CHUNK_TYPES = [
    "analysis_summary",
    "judgment_reason",
    "recommendation",
    "anomaly_details",
]


class RagSearchServiceError(Exception):
    """RAG検索Serviceの共通エラー。"""


class RagSearchQueryError(RagSearchServiceError):
    """検索条件が不正な場合のエラー。"""


class RagSearchEmbeddingError(RagSearchServiceError):
    """検索文のEmbedding生成に失敗した場合のエラー。"""


@dataclass(frozen=True)
class RagSearchResult:
    """RAG検索結果1件。"""

    report_chunk: object
    distance: float
    similarity: float


class RagSearchService:
    """検索文のEmbedding生成と類似チャンク検索を担当する。"""

    def __init__(
        self,
        session,
        azure_openai_service=None,
    ):
        self._vector_repository = VectorRepository(
            session
        )
        self._azure_openai_service = (
            azure_openai_service
            if azure_openai_service is not None
            else AzureOpenAIService()
        )

    def search(
        self,
        query,
        *,
        limit=5,
        equipment_id=None,
        measurement_date_from=None,
        measurement_date_to=None,
        chunk_types=None,
    ):
        """検索文に類似する過去レポートチャンクを返す。"""

        normalized_query = self._validate_query(query)
        normalized_limit = self._validate_limit(limit)
        normalized_equipment_id = (
            self._normalize_optional_text(equipment_id)
        )
        normalized_chunk_types = self._validate_chunk_types(
            chunk_types
        )
        self._validate_date_range(
            measurement_date_from,
            measurement_date_to,
        )

        try:
            query_embedding = (
                self._azure_openai_service.create_embedding(
                    normalized_query
                )
            )
        except AzureOpenAIServiceError as exc:
            raise RagSearchEmbeddingError(
                "検索文のEmbedding生成に失敗しました。"
                f" cause={type(exc).__name__}"
            ) from exc

        rows = self._vector_repository.search_similar(
            query_embedding=query_embedding,
            limit=normalized_limit,
            equipment_id=normalized_equipment_id,
            measurement_date_from=measurement_date_from,
            measurement_date_to=measurement_date_to,
            chunk_types=normalized_chunk_types,
        )

        return [
            RagSearchResult(
                report_chunk=row["report_chunk"],
                distance=float(row["distance"]),
                similarity=self._to_similarity(
                    row["distance"]
                ),
            )
            for row in rows
        ]

    @staticmethod
    def _validate_query(query) -> str:
        if not isinstance(query, str):
            raise RagSearchQueryError(
                "queryは文字列で指定してください。"
            )

        normalized_query = query.strip()
        if not normalized_query:
            raise RagSearchQueryError(
                "queryを空にできません。"
            )

        if len(normalized_query) > 2000:
            raise RagSearchQueryError(
                "queryは2000文字以内で指定してください。"
            )

        return normalized_query

    @staticmethod
    def _validate_limit(limit) -> int:
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise RagSearchQueryError(
                "limitは整数で指定してください。"
            )

        if limit < 1 or limit > 20:
            raise RagSearchQueryError(
                "limitは1以上20以下で指定してください。"
            )

        return limit

    @staticmethod
    def _normalize_optional_text(value):
        if value is None:
            return None

        if not isinstance(value, str):
            raise RagSearchQueryError(
                "equipment_idは文字列で指定してください。"
            )

        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _validate_chunk_types(chunk_types):
        if chunk_types is None:
            return list(DEFAULT_CHUNK_TYPES)

        if not isinstance(chunk_types, list):
            raise RagSearchQueryError(
                "chunk_typesはリストで指定してください。"
            )

        normalized = []
        for chunk_type in chunk_types:
            if not isinstance(chunk_type, str):
                raise RagSearchQueryError(
                    "chunk_typesには文字列を指定してください。"
                )

            value = chunk_type.strip()
            if value and value not in normalized:
                normalized.append(value)

        if not normalized:
            raise RagSearchQueryError(
                "chunk_typesを空にできません。"
            )

        return normalized

    @staticmethod
    def _validate_date_range(
        measurement_date_from,
        measurement_date_to,
    ) -> None:
        for value, field_name in (
            (measurement_date_from, "measurement_date_from"),
            (measurement_date_to, "measurement_date_to"),
        ):
            if value is not None and not isinstance(value, date):
                raise RagSearchQueryError(
                    f"{field_name}はdate型で指定してください。"
                )

        if (
            measurement_date_from is not None
            and measurement_date_to is not None
            and measurement_date_from > measurement_date_to
        ):
            raise RagSearchQueryError(
                "検索開始日は検索終了日以前にしてください。"
            )

    @staticmethod
    def _to_similarity(distance) -> float:
        value = 1.0 - float(distance)
        return round(max(0.0, min(1.0, value)), 6)
