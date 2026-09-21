"""CSV分析・レポート生成LangGraphのState定義。"""

from datetime import date
from typing import NotRequired, Required, TypedDict
from uuid import UUID

import pandas as pd

from backend.src.models.report import Report
from backend.src.models.report_chunk import ReportChunk
from backend.src.models.uploaded_file import UploadedFile
from backend.src.services.vibration_analysis_service import (
    VibrationAnalysisResult,
)


class ReportChunkData(TypedDict):
    """保存前のレポートチャンク。"""

    chunk_index: int
    chunk_type: str
    content: str
    metadata_json: dict[str, object]


class EmbeddedReportChunkData(ReportChunkData):
    """Embedding生成済みのレポートチャンク。"""

    embedding: list[float]
    embedding_model: str
    embedding_dimensions: int


class AnalysisState(TypedDict, total=False):
    """CSV分析からレポート保存まで、Node間で共有する状態。"""

    uploaded_file_id: Required[UUID]
    created_by: Required[UUID]
    threshold_value: Required[float]
    weather: Required[str | None]

    uploaded_file: NotRequired[UploadedFile]
    csv_path: NotRequired[str]
    encoding: NotRequired[str]
    equipment_id: NotRequired[str]
    measurement_date: NotRequired[date | None]

    dataframe: NotRequired[pd.DataFrame]
    analysis_result: NotRequired[VibrationAnalysisResult]

    ai_analysis_text: NotRequired[str]
    ai_summary: NotRequired[str]
    recommendation: NotRequired[str | None]
    report_text: NotRequired[str]

    report: NotRequired[Report]
    report_id: NotRequired[UUID]
    report_chunk: NotRequired[ReportChunk]
    report_chunk_id: NotRequired[UUID]

    report_chunks: NotRequired[list[ReportChunkData]]
    embedded_report_chunks: NotRequired[list[EmbeddedReportChunkData]]
    saved_report_chunks: NotRequired[list[ReportChunk]]

    embedding: NotRequired[list[float]]
    embedding_model: NotRequired[str]
    embedding_dimensions: NotRequired[int]


class AnalysisInputState(TypedDict):
    """分析Graphが外部から受け取る入力。"""

    uploaded_file_id: UUID
    created_by: UUID
    threshold_value: float
    weather: str | None


class AnalysisOutputState(TypedDict):
    """分析Graphが正常終了時に返す出力。"""

    report: Report
    report_chunk: ReportChunk
    analysis_result: VibrationAnalysisResult
    ai_analysis_text: str
    embedding_model: str
    embedding_dimensions: int
