from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError

from backend.src.exceptions.report_exceptions import (
    ReportAlreadyExistsError,
    ReportDatabaseError,
    ReportGenerationError,
    ReportPhysicalFileNotFoundError,
    ReportSourceFileNotFoundError,
)
from backend.src.repositories.uploaded_file_repository import (
    UploadedFileRepository,
)
from backend.src.services.azure_openai_service import (
    AzureOpenAIService,
    AzureOpenAIServiceError,
)
from backend.src.services.csv_service import (
    CsvService,
    CsvServiceError,
)
from backend.src.services.vibration_analysis_service import (
    VibrationAnalysisService,
    VibrationAnalysisServiceError,
)
from backend.src.workflows.graphs.analysis_graph import (
    build_analysis_graph,
)


@dataclass(frozen=True)
class ReportGenerationResult:
    """レポート生成結果。"""

    report: object
    report_chunk: object
    analysis_result: object
    ai_analysis_text: str


class ReportService:
    """LangGraphによるレポート生成とトランザクションを管理する。"""

    def __init__(
        self,
        session,
        csv_service=None,
        analysis_service=None,
        azure_openai_service=None,
    ):
        self._session = session
        self._file_repository = UploadedFileRepository(
            session
        )

        self._csv_service = (
            csv_service
            if csv_service is not None
            else CsvService()
        )
        self._analysis_service = (
            analysis_service
            if analysis_service is not None
            else VibrationAnalysisService()
        )
        self._azure_openai_service = (
            azure_openai_service
            if azure_openai_service is not None
            else AzureOpenAIService()
        )

        self._analysis_graph = build_analysis_graph(
            session=self._session,
            csv_service=self._csv_service,
            analysis_service=self._analysis_service,
            azure_openai_service=(
                self._azure_openai_service
            ),
        )

    def generate_report(
        self,
        uploaded_file_id,
        created_by,
        threshold_value,
        weather=None,
    ):
        """LangGraphを使用してAIレポートを生成する。"""

        graph_input = {
            "uploaded_file_id": uploaded_file_id,
            "created_by": created_by,
            "threshold_value": threshold_value,
            "weather": weather,
        }

        try:
            graph_result = self._analysis_graph.invoke(
                graph_input
            )

            self._session.commit()

            report = graph_result["report"]
            report_chunk = graph_result["report_chunk"]

            self._session.refresh(report)
            self._session.refresh(report_chunk)

            return ReportGenerationResult(
                report=report,
                report_chunk=report_chunk,
                analysis_result=(
                    graph_result["analysis_result"]
                ),
                ai_analysis_text=(
                    graph_result["ai_analysis_text"]
                ),
            )

        except (
            ReportSourceFileNotFoundError,
            ReportPhysicalFileNotFoundError,
            ReportAlreadyExistsError,
        ):
            self._session.rollback()
            raise

        except (
            CsvServiceError,
            VibrationAnalysisServiceError,
            AzureOpenAIServiceError,
        ) as exc:
            self._session.rollback()

            self._save_failure_status(
                uploaded_file_id=uploaded_file_id,
                error_code=type(exc).__name__,
                error_message=str(exc),
            )

            raise ReportGenerationError(
                "レポート生成処理に失敗しました。"
                f" cause={type(exc).__name__}"
            ) from exc

        except IntegrityError as exc:
            self._session.rollback()

            self._save_failure_status(
                uploaded_file_id=uploaded_file_id,
                error_code="IntegrityError",
                error_message=(
                    "レポートまたはチャンクの"
                    "DB登録に失敗しました。"
                ),
            )

            raise ReportDatabaseError(
                "レポートのDB登録に失敗しました。"
            ) from exc

        except Exception as exc:
            self._session.rollback()

            self._save_failure_status(
                uploaded_file_id=uploaded_file_id,
                error_code=type(exc).__name__,
                error_message=str(exc),
            )

            raise ReportGenerationError(
                "予期しないエラーにより"
                "レポート生成に失敗しました。"
                f" cause={type(exc).__name__}"
            ) from exc

    def _save_failure_status(
        self,
        uploaded_file_id,
        error_code,
        error_message,
    ):
        """失敗状態を別トランザクションで保存する。"""

        uploaded_file = (
            self._file_repository.get_by_id(
                uploaded_file_id
            )
        )

        if uploaded_file is None:
            return

        safe_error_code = (
            str(error_code)[:100]
            if error_code
            else "UnknownError"
        )
        safe_error_message = (
            str(error_message)[:2000]
            if error_message
            else "エラー詳細なし"
        )

        try:
            self._file_repository.update_status(
                uploaded_file,
                status="failed",
                error_code=safe_error_code,
                error_message=safe_error_message,
            )
            self._session.commit()

        except Exception:
            # 想定外の例外でもTransactionを確実にRollbackし、
            # 元の例外をそのまま呼び出し元へ再送出する。
            self._session.rollback()
            raise
