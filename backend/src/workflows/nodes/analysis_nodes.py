"""CSV取得・検証・振動分析・AI分析を担当するLangGraph Node。"""

from pathlib import Path

from backend.src.exceptions.report_exceptions import (
    ReportAlreadyExistsError,
    ReportPhysicalFileNotFoundError,
    ReportSourceFileNotFoundError,
)
from backend.src.repositories.report_repository import (
    ReportRepository,
)
from backend.src.repositories.uploaded_file_repository import (
    UploadedFileRepository,
)
from backend.src.services.azure_openai_service import (
    AzureOpenAIService,
)
from backend.src.services.csv_service import CsvService
from backend.src.services.vibration_analysis_service import (
    VibrationAnalysisService,
)
from backend.src.workflows.states.analysis_state import (
    AnalysisState,
)

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class AnalysisNodes:
    """分析ワークフローで使用するNode群。"""

    def __init__(
        self,
        session,
        csv_service=None,
        analysis_service=None,
        azure_openai_service=None,
    ):
        self._file_repository = UploadedFileRepository(
            session
        )
        self._report_repository = ReportRepository(
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

    def load_uploaded_file(
        self,
        state: AnalysisState,
    ) -> dict:
        """CSV管理情報を取得し、関連情報をStateへ追加する。"""

        uploaded_file = self._file_repository.get_by_id(
            state["uploaded_file_id"]
        )

        if uploaded_file is None:
            raise ReportSourceFileNotFoundError(
                "指定されたCSV管理情報が存在しません。"
                f" uploaded_file_id={state['uploaded_file_id']}"
            )

        csv_path = self._resolve_csv_path(
            uploaded_file.file_path
        )

        if not csv_path.exists():
            raise ReportPhysicalFileNotFoundError(
                "CSV実ファイルが存在しません。"
                f" path={csv_path}"
            )

        if not csv_path.is_file():
            raise ReportPhysicalFileNotFoundError(
                "CSVの保存先がファイルではありません。"
                f" path={csv_path}"
            )

        return {
            "uploaded_file": uploaded_file,
            "csv_path": str(csv_path),
            "encoding": uploaded_file.encoding,
            "equipment_id": uploaded_file.equipment_id,
            "measurement_date": uploaded_file.measurement_date,
        }

    def check_existing_report(
        self,
        state: AnalysisState,
    ) -> dict:
        """同一CSVのレポートが登録済みでないことを確認する。"""

        uploaded_file = state["uploaded_file"]
        existing_report = (
            self._report_repository
            .get_by_uploaded_file_id(
                uploaded_file.id
            )
        )

        if existing_report is not None:
            raise ReportAlreadyExistsError(
                "対象CSVのレポートは"
                "既に作成されています。"
                f" report_id={existing_report.id}"
            )

        return {}

    def mark_processing(
        self,
        state: AnalysisState,
    ) -> dict:
        """CSV管理情報の処理状態をprocessingへ更新する。"""

        uploaded_file = state["uploaded_file"]
        updated_file = self._file_repository.update_status(
            uploaded_file,
            status="processing",
            error_code=None,
            error_message=None,
        )

        return {
            "uploaded_file": updated_file,
        }

    def load_and_validate_csv(
        self,
        state: AnalysisState,
    ) -> dict:
        """CSVを読み込み、検証済みDataFrameをStateへ追加する。"""

        dataframe = self._csv_service.load(
            Path(state["csv_path"]),
            encoding=state["encoding"],
        )

        return {
            "dataframe": dataframe,
        }

    def analyze_vibration(
        self,
        state: AnalysisState,
    ) -> dict:
        """振動値の統計計算と閾値判定を実行する。"""

        analysis_result = self._analysis_service.analyze(
            state["dataframe"],
            threshold_value=state["threshold_value"],
        )

        return {
            "analysis_result": analysis_result,
        }

    def generate_ai_analysis(
        self,
        state: AnalysisState,
    ) -> dict:
        """振動統計情報からAI分析文を生成する。"""

        analysis_result = state["analysis_result"]
        ai_analysis_text = (
            self._azure_openai_service
            .generate_vibration_analysis(
                equipment_id=state["equipment_id"],
                measurement_date=state["measurement_date"],
                record_count=analysis_result.record_count,
                minimum_value=analysis_result.minimum_value,
                maximum_value=analysis_result.maximum_value,
                average_value=analysis_result.average_value,
                median_value=analysis_result.median_value,
                standard_deviation=(
                    analysis_result.standard_deviation
                ),
                threshold_value=analysis_result.threshold_value,
                anomaly_count=analysis_result.anomaly_count,
            )
        )

        return {
            "ai_analysis_text": ai_analysis_text,
        }

    @staticmethod
    def _resolve_csv_path(stored_path) -> Path:
        """DBの保存パスを絶対パスへ変換する。"""

        path = Path(stored_path)

        if path.is_absolute():
            return path

        return PROJECT_ROOT / path
