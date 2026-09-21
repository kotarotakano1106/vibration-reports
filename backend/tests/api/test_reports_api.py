import hashlib
import uuid
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.src.repositories.report_repository import ReportRepository
from backend.src.repositories.uploaded_file_repository import UploadedFileRepository
from backend.src.repositories.user_repository import UserRepository


def create_report(db_session: Session, *, equipment_id: str = "MOTOR-API-001"):
    """一覧API確認用のレポートと元CSVを作成する。"""
    suffix = uuid.uuid4().hex
    user = UserRepository(db_session).create(
        login_id=f"reports-api-{suffix}",
        password_hash="hashed-password",
        display_name="Report一覧APIテストユーザー",
    )
    stored_filename = f"{uuid.uuid4()}.csv"
    uploaded_file = UploadedFileRepository(db_session).create(
        uploaded_by=user.id,
        equipment_id=equipment_id,
        original_filename="measurement.csv",
        stored_filename=stored_filename,
        file_path=f"data/uploads/{stored_filename}",
        file_size=128,
        checksum=hashlib.sha256(uuid.uuid4().bytes).hexdigest(),
        measurement_date=date(2026, 9, 1),
        mime_type="text/csv",
        status="completed",
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
        standard_deviation=0.8,
        threshold_value=2.5,
        anomaly_count=1,
        anomaly_details=[],
        status="requires_attention",
        ai_summary="振動値の上昇を確認しました。",
        ai_analysis="閾値超過が1件あります。",
        recommendation="設備を点検してください。",
        report_text="振動分析レポート本文",
        measurement_date=date(2026, 9, 1),
    )
    return report, uploaded_file


def test_list_reports_returns_empty_list(api_client: TestClient) -> None:
    """レポートがない場合は空配列を返す。"""
    response = api_client.get("/api/v1/reports")

    assert response.status_code == 200
    assert response.json() == []


def test_list_reports_returns_report_summary(
    api_client: TestClient,
    db_session: Session,
) -> None:
    """レポート概要と元CSV名を返す。"""
    report, uploaded_file = create_report(db_session)

    response = api_client.get("/api/v1/reports")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    item = body[0]
    assert item["id"] == str(report.id)
    assert item["uploaded_file_id"] == str(uploaded_file.id)
    assert item["equipment_id"] == "MOTOR-API-001"
    assert item["measurement_date"] == "2026-09-01"
    assert item["title"] == "振動分析レポート"
    assert item["anomaly_count"] == 1
    assert item["status"] == "requires_attention"
    assert item["original_filename"] == "measurement.csv"
    assert item["threshold_value"] == 2.5


def test_list_reports_applies_limit_and_offset(
    api_client: TestClient,
    db_session: Session,
) -> None:
    """limitとoffsetで一覧を分割できる。"""
    first, _ = create_report(db_session, equipment_id="MOTOR-API-001")
    second, _ = create_report(db_session, equipment_id="MOTOR-API-002")

    response = api_client.get("/api/v1/reports?limit=1&offset=1")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] in {str(first.id), str(second.id)}


def test_list_reports_normalizes_invalid_pagination(
    api_client: TestClient,
    db_session: Session,
) -> None:
    """負のoffsetと0のlimitを安全な値へ補正する。"""
    report, _ = create_report(db_session)

    response = api_client.get("/api/v1/reports?limit=0&offset=-1")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == str(report.id)
