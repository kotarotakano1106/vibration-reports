from datetime import date, datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
)


class MeasurementPointResponse(BaseModel):
    """1件分の振動測定値。"""

    measured_at: datetime

    vibration_value: float

    is_anomaly: bool


class MeasurementDataResponse(BaseModel):
    """グラフ表示用の振動測定データ。"""

    uploaded_file_id: UUID

    equipment_id: str

    measurement_date: date | None

    measurement_count: int = Field(
        ge=0,
    )

    threshold_value: float = Field(
        gt=0,
    )

    measurements: list[
        MeasurementPointResponse
    ]