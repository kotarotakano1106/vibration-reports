from pathlib import Path
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from backend.src.db.dependencies import (
    get_db_session,
)
from backend.src.repositories.uploaded_file_repository import (
    UploadedFileRepository,
)
from backend.src.schemas.measurement_schema import (
    MeasurementDataResponse,
    MeasurementPointResponse,
)
from backend.src.services.csv_service import (
    CsvService,
    CsvServiceError,
)

PROJECT_ROOT = Path(__file__).resolve().parents[4]


router = APIRouter(
    prefix="/files",
    tags=["measurements"],
)


@router.get(
    "/{uploaded_file_id}/measurements",
    response_model=MeasurementDataResponse,
    status_code=status.HTTP_200_OK,
)
def get_measurements(
    uploaded_file_id: UUID,
    threshold_value: float = Query(
        default=2.0,
        gt=0,
        description=(
            "異常判定に使用する"
            "振動値の閾値"
        ),
    ),
    session: Session = Depends(
        get_db_session,
    ),
):
    """保存済みCSVからグラフ表示用測定値を取得する。"""

    repository = UploadedFileRepository(
        session,
    )

    uploaded_file = repository.get_by_id(
        uploaded_file_id,
    )

    if uploaded_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "指定されたCSV管理情報が"
                "存在しません。"
                f" uploaded_file_id={uploaded_file_id}"
            ),
        )

    csv_path = _resolve_csv_path(
        uploaded_file.file_path,
    )

    if not csv_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "CSV実ファイルが存在しません。"
                f" path={csv_path}"
            ),
        )

    if not csv_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "CSVの保存先が"
                "ファイルではありません。"
                f" path={csv_path}"
            ),
        )

    csv_service = CsvService()

    try:
        dataframe = csv_service.load(
            csv_path,
            encoding=uploaded_file.encoding,
        )

    except CsvServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    measurements = []

    for row in dataframe.itertuples(
        index=False,
    ):
        measured_at = getattr(
            row,
            CsvService.DATETIME_COLUMN,
        )

        vibration_value = float(
            getattr(
                row,
                CsvService.VALUE_COLUMN,
            )
        )

        measurement = MeasurementPointResponse(
            measured_at=measured_at,
            vibration_value=vibration_value,
            is_anomaly=(
                vibration_value
                > threshold_value
            ),
        )

        measurements.append(
            measurement
        )

    return MeasurementDataResponse(
        uploaded_file_id=uploaded_file.id,
        equipment_id=uploaded_file.equipment_id,
        measurement_date=(
            uploaded_file.measurement_date
        ),
        measurement_count=len(
            measurements
        ),
        threshold_value=threshold_value,
        measurements=measurements,
    )


def _resolve_csv_path(
    stored_path,
):
    """DB上の保存パスを絶対パスへ変換する。"""

    path = Path(
        stored_path
    )

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path