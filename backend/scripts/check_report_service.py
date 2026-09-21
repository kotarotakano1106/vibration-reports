from datetime import date

from sqlalchemy import select

from backend.src.db.session import SessionLocal
from backend.src.models.uploaded_file import UploadedFile
from backend.src.repositories.report_repository import (
    ReportRepository,
)
from backend.src.repositories.user_repository import (
    UserRepository,
)
from backend.src.services.report_service import (
    ReportAlreadyExistsError,
    ReportService,
    ReportServiceError,
)


TEST_LOGIN_ID = "dev-user"
TEST_EQUIPMENT_ID = "MOTOR-TEST-002"

TEST_MEASUREMENT_DATE = date(
    2026,
    9,
    9,
)


def get_target_uploaded_file(session):
    """FileServiceで登録した対象CSVを取得する。"""

    statement = (
        select(UploadedFile)
        .where(
            UploadedFile.equipment_id
            == TEST_EQUIPMENT_ID,
            UploadedFile.measurement_date
            == TEST_MEASUREMENT_DATE,
        )
        .order_by(
            UploadedFile.uploaded_at.desc()
        )
        .limit(1)
    )

    return session.scalar(statement)


def show_existing_report(report):
    """登録済みレポートを表示する。"""

    print()
    print("対象CSVのレポートは登録済みです。")
    print("report_id:", report.id)
    print("title:", report.title)
    print("status:", report.status)
    print("record_count:", report.record_count)
    print("maximum_value:", report.maximum_value)
    print("anomaly_count:", report.anomaly_count)
    print("ai_model:", report.ai_model)


def show_generation_result(result):
    """新しく生成したレポート情報を表示する。"""

    report = result.report
    report_chunk = result.report_chunk
    analysis = result.analysis_result

    print()
    print("レポート生成: 成功")
    print("report_id:", report.id)
    print(
        "uploaded_file_id:",
        report.uploaded_file_id,
    )
    print(
        "created_by:",
        report.created_by,
    )
    print(
        "equipment_id:",
        report.equipment_id,
    )
    print(
        "measurement_date:",
        report.measurement_date,
    )
    print("title:", report.title)
    print("status:", report.status)
    print("record_count:", report.record_count)
    print(
        "minimum_value:",
        report.minimum_value,
    )
    print(
        "maximum_value:",
        report.maximum_value,
    )
    print(
        "average_value:",
        report.average_value,
    )
    print(
        "median_value:",
        report.median_value,
    )
    print(
        "standard_deviation:",
        report.standard_deviation,
    )
    print(
        "threshold_value:",
        report.threshold_value,
    )
    print(
        "anomaly_count:",
        report.anomaly_count,
    )
    print("ai_model:", report.ai_model)
    print(
        "prompt_version:",
        report.prompt_version,
    )

    print()
    print("Embedding保存: 成功")
    print(
        "report_chunk_id:",
        report_chunk.id,
    )
    print(
        "chunk_index:",
        report_chunk.chunk_index,
    )
    print(
        "chunk_type:",
        report_chunk.chunk_type,
    )
    print(
        "embedding_model:",
        report_chunk.embedding_model,
    )

    print()
    print("振動分析結果:")
    print(
        "分析上の異常件数:",
        analysis.anomaly_count,
    )
    print(
        "分析上の異常率:",
        analysis.anomaly_rate,
    )
    print(
        "分析上の判定:",
        analysis.status,
    )

    print()
    print("AI分析文章:")
    print(result.ai_analysis_text)


def main():
    """ReportServiceの結合動作を確認する。"""

    with SessionLocal() as session:
        user_repository = UserRepository(
            session
        )

        report_repository = ReportRepository(
            session
        )

        user = user_repository.get_by_login_id(
            TEST_LOGIN_ID
        )

        if user is None:
            raise RuntimeError(
                "dev-userが存在しません。"
                "UserRepositoryの確認を"
                "先に実行してください。"
            )

        uploaded_file = get_target_uploaded_file(
            session
        )

        if uploaded_file is None:
            raise RuntimeError(
                f"{TEST_MEASUREMENT_DATE}の"
                f"{TEST_EQUIPMENT_ID}に対応する"
                "CSV管理情報が存在しません。"
            )

        print("=== ReportService結合確認 ===")
        print("created_by:", user.id)
        print(
            "uploaded_file_id:",
            uploaded_file.id,
        )
        print(
            "CSVファイル:",
            uploaded_file.file_path,
        )
        print(
            "現在のCSV処理状態:",
            uploaded_file.status,
        )

        existing_report = (
            report_repository
            .get_by_uploaded_file_id(
                uploaded_file.id
            )
        )

        if existing_report is not None:
            show_existing_report(
                existing_report
            )
            return

        service = ReportService(session)

        result = service.generate_report(
            uploaded_file_id=uploaded_file.id,
            created_by=user.id,
            threshold_value=2.0,
            weather="晴れ",
        )

        show_generation_result(result)

        refreshed_file = session.get(
            UploadedFile,
            uploaded_file.id,
        )

        if refreshed_file is None:
            raise RuntimeError(
                "CSV管理情報を"
                "再取得できませんでした。"
            )

        print()
        print(
            "CSV処理状態:",
            refreshed_file.status,
        )

        if refreshed_file.status != "completed":
            raise RuntimeError(
                "CSV処理状態が"
                "completedではありません。"
            )

        if result.report_chunk.chunk_index != 0:
            raise RuntimeError(
                "チャンク番号が"
                "0ではありません。"
            )

        if (
            result.report_chunk.chunk_type
            != "full_report"
        ):
            raise RuntimeError(
                "チャンク種別が"
                "full_reportではありません。"
            )

        print()
        print("ReportService結合確認: 成功")


if __name__ == "__main__":
    try:
        main()

    except ReportAlreadyExistsError as exc:
        print(
            "登録済みレポート:",
            str(exc),
        )

    except ReportServiceError as exc:
        print(
            "ReportService確認失敗:",
            type(exc).__name__,
            str(exc),
        )
        raise SystemExit(1) from exc

    except Exception as exc:
        print(
            "予期しないエラー:",
            type(exc).__name__,
            str(exc),
        )
        raise SystemExit(1) from exc