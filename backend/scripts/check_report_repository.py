from datetime import datetime

from sqlalchemy.exc import IntegrityError

from backend.src.db.session import SessionLocal
from backend.src.repositories.report_repository import (
    ReportRepository,
)
from backend.src.repositories.uploaded_file_repository import (
    UploadedFileRepository,
)
from backend.src.repositories.user_repository import (
    UserRepository,
)


TEST_LOGIN_ID = "dev-user"
TEST_EQUIPMENT_ID = "MOTOR-001"


def show_report(report):
    """秘密情報を除いてレポート情報を表示する。"""

    print("ID:", report.id)
    print(
        "uploaded_file_id:",
        report.uploaded_file_id,
    )
    print("created_by:", report.created_by)
    print("equipment_id:", report.equipment_id)
    print(
        "measurement_date:",
        report.measurement_date,
    )
    print("title:", report.title)
    print("record_count:", report.record_count)
    print("minimum_value:", report.minimum_value)
    print("maximum_value:", report.maximum_value)
    print("average_value:", report.average_value)
    print(
        "standard_deviation:",
        report.standard_deviation,
    )
    print(
        "threshold_value:",
        report.threshold_value,
    )
    print("anomaly_count:", report.anomaly_count)
    print("status:", report.status)
    print("ai_model:", report.ai_model)
    print(
        "prompt_version:",
        report.prompt_version,
    )
    print("pdf_path:", report.pdf_path)
    print("created_at:", report.created_at)


def main():
    """レポートの登録・取得・更新を確認する。"""

    with SessionLocal() as session:
        user_repository = UserRepository(session)

        file_repository = UploadedFileRepository(
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
            )

        uploaded_files = (
            file_repository.list_by_equipment_id(
                TEST_EQUIPMENT_ID,
                limit=1,
            )
        )

        if not uploaded_files:
            raise RuntimeError(
                "MOTOR-001のCSV管理情報がありません。"
                "UploadedFileRepositoryの確認を"
                "先に実行してください。"
            )

        uploaded_file = uploaded_files[0]

        existing_report = (
            report_repository.get_by_uploaded_file_id(
                uploaded_file.id
            )
        )

        if existing_report is not None:
            print(
                "登録済みレポートを取得しました。"
            )
            show_report(existing_report)
            return

        anomaly_details = [
            {
                "measured_at": (
                    "2026-09-01T09:00:20+09:00"
                ),
                "value": 2.5,
                "threshold": 2.0,
            }
        ]

        try:
            created_report = report_repository.create(
                uploaded_file_id=uploaded_file.id,
                created_by=user.id,
                equipment_id=uploaded_file.equipment_id,
                measurement_date=(
                    uploaded_file.measurement_date
                ),
                weather="晴れ",
                title=(
                    "MOTOR-001 振動分析レポート"
                ),
                record_count=3,
                minimum_value=0.4,
                maximum_value=2.5,
                average_value=1.1667,
                median_value=0.6,
                standard_deviation=0.9437,
                threshold_value=2.0,
                anomaly_count=1,
                anomaly_details=anomaly_details,
                status="requires_attention",
                ai_summary=(
                    "振動値が一時的に閾値を"
                    "超過しました。"
                ),
                ai_analysis=(
                    "3件の測定値のうち1件で、"
                    "設定した閾値2.0を超える"
                    "振動値2.5を検出しました。"
                ),
                recommendation=(
                    "設備の固定部分を確認し、"
                    "再測定してください。"
                ),
                report_text=(
                    "MOTOR-001の振動測定では、"
                    "最大値2.5を記録しました。"
                    "閾値超過を1件検出したため、"
                    "設備点検と再測定を推奨します。"
                ),
                ai_model="gpt-5.4-mini",
                prompt_version="v1",
            )

            session.commit()
            session.refresh(created_report)

        except IntegrityError as exc:
            session.rollback()

            raise RuntimeError(
                "レポート登録に失敗しました。"
                "外部キーまたはDB制約を"
                "確認してください。"
            ) from exc

        retrieved_report = report_repository.get_by_id(
            created_report.id
        )

        if retrieved_report is None:
            raise RuntimeError(
                "登録したレポートを取得できませんでした。"
            )

        print("レポート登録: 成功")
        print("IDによる取得: 成功")
        show_report(retrieved_report)

        report_repository.update_pdf_information(
            retrieved_report,
            pdf_path=(
                "data/reports/"
                f"{retrieved_report.id}.pdf"
            ),
            pdf_generated_at=(
                datetime.now().astimezone()
            ),
        )

        session.commit()
        session.refresh(retrieved_report)

        print("PDF情報更新: 成功")
        print(
            "更新後pdf_path:",
            retrieved_report.pdf_path,
        )
        print(
            "更新後pdf_generated_at:",
            retrieved_report.pdf_generated_at,
        )


if __name__ == "__main__":
    try:
        main()

    except Exception as exc:
        print(
            "ReportRepository確認失敗:",
            type(exc).__name__,
            str(exc),
        )

        raise SystemExit(1) from exc