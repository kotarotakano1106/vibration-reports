import hashlib
import uuid
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.src.repositories.report_repository import ReportRepository
from backend.src.repositories.uploaded_file_repository import UploadedFileRepository
from backend.src.repositories.user_repository import UserRepository


def unique_text(prefix: str) -> str:
    """テストごとに一意な文字列を生成する。"""
    return f"{prefix}-{uuid.uuid4().hex}"


def create_test_user(db_session: Session):
    """テスト用ユーザーを作成する。"""
    return UserRepository(db_session).create(
        login_id=unique_text("report-user"),
        password_hash="hashed-password",
        display_name="レポートテストユーザー",
    )


def create_test_uploaded_file(
    db_session: Session,
    *,
    equipment_id: str = "MOTOR-001",
):
    """テスト用CSV管理情報を作成する。"""
    user = create_test_user(db_session)
    stored_filename = f"{uuid.uuid4()}.csv"
    checksum = hashlib.sha256(uuid.uuid4().bytes).hexdigest()

    uploaded_file = UploadedFileRepository(db_session).create(
        uploaded_by=user.id,
        equipment_id=equipment_id,
        original_filename="measurement.csv",
        stored_filename=stored_filename,
        file_path=f"data/uploads/{stored_filename}",
        file_size=128,
        checksum=checksum,
        measurement_date=date(2026, 9, 1),
        mime_type="text/csv",
        encoding="UTF-8",
        status="completed",
    )
    return user, uploaded_file


def create_test_report(
    db_session: Session,
    *,
    equipment_id: str = "MOTOR-001",
    created_at: datetime | None = None,
):
    """テスト用レポートを作成する。"""
    user, uploaded_file = create_test_uploaded_file(
        db_session,
        equipment_id=equipment_id,
    )
    report = ReportRepository(db_session).create(
        uploaded_file_id=uploaded_file.id,
        created_by=user.id,
        equipment_id=equipment_id,
        title="振動分析レポート",
        record_count=3,
        minimum_value=1.0,
        maximum_value=3.0,
        average_value=2.0,
        median_value=2.0,
        standard_deviation=0.8164965809,
        threshold_value=2.5,
        anomaly_count=1,
        anomaly_details=[
            {
                "row_number": 4,
                "measured_at": "2026-09-01T10:00:02+09:00",
                "value": 3.0,
            }
        ],
        status="requires_attention",
        ai_summary="振動値の上昇を確認しました。",
        ai_analysis="閾値を超える測定値が1件あります。",
        recommendation="設備を点検してください。",
        report_text="振動分析レポート本文",
        measurement_date=date(2026, 9, 1),
        weather="晴れ",
        ai_model="test-model",
        prompt_version="v1",
    )
    if created_at is not None:
        report.created_at = created_at
        db_session.flush()
    return user, uploaded_file, report


def test_create_and_get_by_id(db_session: Session) -> None:
    """レポートを登録し、UUIDで取得できる。"""
    repository = ReportRepository(db_session)
    _, uploaded_file, created = create_test_report(db_session)

    found = repository.get_by_id(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.uploaded_file_id == uploaded_file.id
    assert found.title == "振動分析レポート"
    assert found.record_count == 3
    assert found.anomaly_count == 1
    assert found.status == "requires_attention"


def test_get_by_uploaded_file_id(db_session: Session) -> None:
    """アップロードファイルIDでレポートを取得できる。"""
    repository = ReportRepository(db_session)
    _, uploaded_file, created = create_test_report(db_session)

    found = repository.get_by_uploaded_file_id(uploaded_file.id)

    assert found is not None
    assert found.id == created.id


def test_get_returns_none_for_unknown_values(db_session: Session) -> None:
    """存在しない条件ではNoneを返す。"""
    repository = ReportRepository(db_session)

    assert repository.get_by_id(uuid.uuid4()) is None
    assert repository.get_by_uploaded_file_id(uuid.uuid4()) is None


def test_list_by_equipment_id(db_session: Session) -> None:
    """指定設備のレポートだけを取得できる。"""
    repository = ReportRepository(db_session)
    _, _, first = create_test_report(
        db_session,
        equipment_id="MOTOR-REPORT-LIST",
    )
    _, _, second = create_test_report(
        db_session,
        equipment_id="MOTOR-REPORT-LIST",
    )
    create_test_report(
        db_session,
        equipment_id="MOTOR-REPORT-OTHER",
    )

    result = repository.list_by_equipment_id("MOTOR-REPORT-LIST")
    result_ids = {item.id for item in result}

    assert first.id in result_ids
    assert second.id in result_ids
    assert all(item.equipment_id == "MOTOR-REPORT-LIST" for item in result)


def test_list_by_equipment_id_applies_limit_and_offset(
    db_session: Session,
) -> None:
    """設備別一覧でlimitとoffsetが機能する。"""
    repository = ReportRepository(db_session)
    base_time = datetime.now().astimezone()
    reports = []

    for index in range(3):
        _, _, report = create_test_report(
            db_session,
            equipment_id="MOTOR-REPORT-PAGING",
            created_at=base_time + timedelta(minutes=index),
        )
        reports.append(report)

    first_page = repository.list_by_equipment_id(
        "MOTOR-REPORT-PAGING",
        limit=2,
        offset=0,
    )
    second_page = repository.list_by_equipment_id(
        "MOTOR-REPORT-PAGING",
        limit=2,
        offset=2,
    )

    assert [item.id for item in first_page] == [reports[2].id, reports[1].id]
    assert [item.id for item in second_page] == [reports[0].id]


def test_list_all_with_files_returns_joined_rows(
    db_session: Session,
) -> None:
    """レポートと元CSVを結合して取得できる。"""
    repository = ReportRepository(db_session)
    _, uploaded_file, report = create_test_report(db_session)

    rows = repository.list_all_with_files(limit=100, offset=0)
    matching = [(r, f) for r, f in rows if r.id == report.id]

    assert len(matching) == 1
    found_report, found_file = matching[0]
    assert found_report.id == report.id
    assert found_file.id == uploaded_file.id
    assert found_file.original_filename == "measurement.csv"


def test_update_pdf_information(db_session: Session) -> None:
    """PDF保存先と生成日時を更新できる。"""
    repository = ReportRepository(db_session)
    _, _, report = create_test_report(db_session)
    generated_at = datetime.now().astimezone()

    updated = repository.update_pdf_information(
        report,
        pdf_path="data/reports/report.pdf",
        pdf_generated_at=generated_at,
    )

    assert updated.pdf_path == "data/reports/report.pdf"
    assert updated.pdf_generated_at == generated_at
    assert updated.updated_at is not None


def test_uploaded_file_id_must_be_unique(db_session: Session) -> None:
    """同じアップロードファイルに複数レポートを登録できない。"""
    repository = ReportRepository(db_session)
    user, uploaded_file, _ = create_test_report(db_session)

    with pytest.raises(IntegrityError):
        repository.create(
            uploaded_file_id=uploaded_file.id,
            created_by=user.id,
            equipment_id="MOTOR-001",
            title="重複レポート",
            record_count=1,
            minimum_value=1.0,
            maximum_value=1.0,
            average_value=1.0,
            anomaly_count=0,
            anomaly_details=[],
            status="normal",
            ai_summary="正常です。",
            ai_analysis="異常はありません。",
            report_text="重複レポート本文",
        )
    db_session.rollback()


@pytest.mark.parametrize(
    ("record_count", "minimum_value", "maximum_value", "anomaly_count"),
    [
        (0, 1.0, 1.0, 0),
        (1, 2.0, 1.0, 0),
        (1, 1.0, 1.0, -1),
    ],
)
def test_report_check_constraints(
    db_session: Session,
    record_count: int,
    minimum_value: float,
    maximum_value: float,
    anomaly_count: int,
) -> None:
    """レポート統計値のCheck制約が機能する。"""
    user, uploaded_file = create_test_uploaded_file(db_session)
    repository = ReportRepository(db_session)

    with pytest.raises(IntegrityError):
        repository.create(
            uploaded_file_id=uploaded_file.id,
            created_by=user.id,
            equipment_id="MOTOR-001",
            title="制約確認レポート",
            record_count=record_count,
            minimum_value=minimum_value,
            maximum_value=maximum_value,
            average_value=1.0,
            anomaly_count=anomaly_count,
            anomaly_details=[],
            status="normal",
            ai_summary="制約確認",
            ai_analysis="制約確認",
            report_text="制約確認",
        )
    db_session.rollback()


def test_unknown_uploaded_file_is_rejected(db_session: Session) -> None:
    """存在しないアップロードファイルIDを拒否する。"""
    user = create_test_user(db_session)
    repository = ReportRepository(db_session)

    with pytest.raises(IntegrityError):
        repository.create(
            uploaded_file_id=uuid.uuid4(),
            created_by=user.id,
            equipment_id="MOTOR-001",
            title="不正FKレポート",
            record_count=1,
            minimum_value=1.0,
            maximum_value=1.0,
            average_value=1.0,
            anomaly_count=0,
            anomaly_details=[],
            status="normal",
            ai_summary="不正FK",
            ai_analysis="不正FK",
            report_text="不正FK",
        )
    db_session.rollback()


def test_unknown_creator_is_rejected(db_session: Session) -> None:
    """存在しない作成者IDを拒否する。"""
    _, uploaded_file = create_test_uploaded_file(db_session)
    repository = ReportRepository(db_session)

    with pytest.raises(IntegrityError):
        repository.create(
            uploaded_file_id=uploaded_file.id,
            created_by=uuid.uuid4(),
            equipment_id="MOTOR-001",
            title="不正作成者レポート",
            record_count=1,
            minimum_value=1.0,
            maximum_value=1.0,
            average_value=1.0,
            anomaly_count=0,
            anomaly_details=[],
            status="normal",
            ai_summary="不正作成者",
            ai_analysis="不正作成者",
            report_text="不正作成者",
        )
    db_session.rollback()


def test_delete_removes_report(db_session: Session) -> None:
    """レポートを削除できる。"""
    repository = ReportRepository(db_session)
    _, _, report = create_test_report(db_session)
    report_id = report.id

    repository.delete(report)

    assert repository.get_by_id(report_id) is None
