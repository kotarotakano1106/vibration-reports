from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReportGenerateRequest(BaseModel):
    """AIレポート生成APIのリクエスト。"""

    uploaded_file_id: UUID

    threshold_value: float = Field(
        gt=0,
        description="振動値の異常判定閾値",
        examples=[2.0],
    )

    weather: str | None = Field(
        default=None,
        max_length=100,
        description="測定日の天候",
        examples=["晴れ"],
    )


class VibrationAnomalyResponse(BaseModel):
    """閾値を超過した測定値。"""

    row_number: int
    measured_at: str
    value: float
    threshold: float
    excess_value: float


class VibrationAnalysisResponse(BaseModel):
    """振動分析結果。"""

    record_count: int
    minimum_value: float
    maximum_value: float
    average_value: float
    median_value: float
    standard_deviation: float
    threshold_value: float
    anomaly_count: int
    anomaly_rate: float
    status: str
    anomalies: list[VibrationAnomalyResponse]


class ReportResponse(BaseModel):
    """レポートAPIのレスポンス。"""

    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID
    uploaded_file_id: UUID
    created_by: UUID
    equipment_id: str
    measurement_date: date | None
    weather: str | None
    title: str

    record_count: int
    minimum_value: float
    maximum_value: float
    average_value: float
    median_value: float | None
    standard_deviation: float | None
    threshold_value: float | None

    anomaly_count: int
    anomaly_details: list[dict]

    status: str
    ai_summary: str
    ai_analysis: str
    recommendation: str | None
    report_text: str

    ai_model: str | None
    prompt_version: str | None

    chart_path: str | None
    pdf_path: str | None
    pdf_generated_at: datetime | None

    created_at: datetime
    updated_at: datetime


class ReportListItemResponse(BaseModel):
    """保存済みレポート一覧APIの1件分。"""

    id: UUID
    uploaded_file_id: UUID
    equipment_id: str
    measurement_date: date | None
    title: str
    anomaly_count: int
    status: str
    created_by: UUID
    created_at: datetime
    original_filename: str
    threshold_value: float | None


class ReportGenerationResponse(BaseModel):
    """AIレポート生成処理のレスポンス。"""

    message: str
    report: ReportResponse
    analysis: VibrationAnalysisResponse

    report_chunk_id: UUID
    embedding_model: str
    embedding_dimensions: int