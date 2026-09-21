"""RAGチャットLangGraphのState定義。"""

from datetime import date
from typing import NotRequired, Required, TypedDict
from uuid import UUID

DEFAULT_CHAT_CHUNK_TYPES = [
    "analysis_summary",
    "judgment_reason",
    "recommendation",
    "anomaly_details",
]


class ChatSearchResult(TypedDict):
    """RAGチャットで使用する類似検索結果1件。"""

    report_chunk_id: UUID
    report_id: UUID
    chunk_index: int
    chunk_type: str
    content: str
    equipment_id: str
    measurement_date: date | None
    distance: float
    similarity: float
    metadata_json: dict[str, object]


class ChatSource(TypedDict):
    """AI回答に添付する参照元情報。"""

    report_chunk_id: UUID
    report_id: UUID
    chunk_type: str
    equipment_id: str
    measurement_date: date | None
    similarity: float


class ChatState(TypedDict, total=False):
    """質問受付から回答生成までNode間で共有する状態。"""

    # Graph入力
    query: Required[str]
    limit: Required[int]
    equipment_id: Required[str | None]
    measurement_date_from: Required[date | None]
    measurement_date_to: Required[date | None]
    chunk_types: Required[list[str]]

    # 検索処理
    search_results: NotRequired[list[ChatSearchResult]]
    has_search_results: NotRequired[bool]

    # 回答生成
    context: NotRequired[str]
    answer: NotRequired[str]
    sources: NotRequired[list[ChatSource]]


class ChatInputState(TypedDict):
    """RAGチャットGraphが外部から受け取る入力。"""

    query: str
    limit: int
    equipment_id: str | None
    measurement_date_from: date | None
    measurement_date_to: date | None
    chunk_types: list[str]


class ChatOutputState(TypedDict):
    """RAGチャットGraphが正常終了時に返す出力。"""

    query: str
    answer: str
    sources: list[ChatSource]
