from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy.orm import Session

from backend.src.db.dependencies import get_db_session
from backend.src.repositories.report_repository import ReportRepository
from backend.src.repositories.user_repository import UserRepository
from backend.src.schemas.report_schema import (
    ReportGenerateRequest,
    ReportGenerationResponse,
    ReportListItemResponse,
    ReportResponse,
    VibrationAnalysisResponse,
)
from backend.src.services.report_pdf_service import (
    ReportPdfNotFoundError,
    ReportPdfService,
    ReportPdfServiceError,
)
from backend.src.services.report_service import (
    ReportAlreadyExistsError,
    ReportDatabaseError,
    ReportGenerationError,
    ReportPhysicalFileNotFoundError,
    ReportService,
    ReportSourceFileNotFoundError,
)

router = APIRouter(prefix="/reports", tags=["reports"])
DEVELOPMENT_LOGIN_ID = "dev-user"
EMBEDDING_DIMENSIONS = 1536


@router.get(
    "",
    response_model=list[ReportListItemResponse],
)
def list_reports(
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(
        get_db_session
    ),
):
    """保存済みレポートを新しい順で取得する。"""

    rows = ReportRepository(
        session
    ).list_all_with_files(
        limit=max(
            1,
            min(limit, 500),
        ),
        offset=max(0, offset),
    )

    return [
        ReportListItemResponse(
            id=report.id,
            uploaded_file_id=report.uploaded_file_id,
            equipment_id=report.equipment_id,
            measurement_date=report.measurement_date,
            title=report.title,
            anomaly_count=report.anomaly_count,
            status=report.status,
            created_by=report.created_by,
            created_at=report.created_at,
            original_filename=uploaded_file.original_filename,
            threshold_value=report.threshold_value,
        )
        for report, uploaded_file in rows
    ]

@router.post(
    "/generate",
    response_model=ReportGenerationResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_report(
    request: ReportGenerateRequest,
    session: Session = Depends(get_db_session),
):
    """保存済みCSVからAIレポートを生成する。"""

    user = UserRepository(session).get_by_login_id(
        DEVELOPMENT_LOGIN_ID
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="開発用ユーザーが登録されていません。",
        )

    try:
        result = ReportService(session).generate_report(
            uploaded_file_id=request.uploaded_file_id,
            created_by=user.id,
            threshold_value=request.threshold_value,
            weather=request.weather,
        )
    except (
        ReportSourceFileNotFoundError,
        ReportPhysicalFileNotFoundError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ReportAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except ReportDatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except ReportGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return ReportGenerationResponse(
        message="AIレポートを生成しました。",
        report=ReportResponse.model_validate(result.report),
        analysis=VibrationAnalysisResponse.model_validate(
            result.analysis_result.to_dict()
        ),
        report_chunk_id=result.report_chunk.id,
        embedding_model=result.report_chunk.embedding_model,
        embedding_dimensions=EMBEDDING_DIMENSIONS,
    )


@router.get("/{report_id}/pdf")
def download_report_pdf(
    report_id: UUID,
    session: Session = Depends(get_db_session),
):
    """指定した振動分析レポートをPDFでダウンロードする。"""

    try:
        pdf_bytes, filename = ReportPdfService(session).generate(
            report_id
        )
    except ReportPdfNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ReportPdfServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            ),
            "Cache-Control": "no-store",
        },
    )
