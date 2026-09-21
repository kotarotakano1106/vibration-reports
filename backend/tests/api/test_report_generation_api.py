import uuid
from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import backend.src.api.v1.reports as reports_module
from backend.src.exceptions.report_exceptions import (
    ReportAlreadyExistsError,
    ReportDatabaseError,
    ReportGenerationError,
    ReportPhysicalFileNotFoundError,
    ReportSourceFileNotFoundError,
)
from backend.src.repositories.user_repository import UserRepository

DEVELOPMENT_LOGIN_ID = "dev-user"


def create_development_user(db_session: Session):
    """APIが参照する開発用ユーザーを作成する。"""
    existing = UserRepository(db_session).get_by_login_id(
        DEVELOPMENT_LOGIN_ID
    )
    if existing is not None:
        return existing

    return UserRepository(db_session).create(
        login_id=DEVELOPMENT_LOGIN_ID,
        password_hash="hashed-password",
        display_name="開発用ユーザー",
    )


def create_generation_result(created_by):
    """ReportGenerationResponseへ変換可能な結果を作成する。"""
    now = datetime.now(UTC)
    uploaded_file_id = uuid.uuid4()
    report = SimpleNamespace(
        id=uuid.uuid4(),
        uploaded_file_id=uploaded_file_id,
        created_by=created_by,
        equipment_id="MOTOR-001",
        measurement_date=date(2026, 9, 1),
        weather="晴れ",
        title="振動分析レポート",
        record_count=3,
        minimum_value=1.0,
        maximum_value=3.0,
        average_value=2.0,
        median_value=2.0,
        standard_deviation=0.816,
        threshold_value=2.0,
        anomaly_count=1,
        anomaly_details=[],
        status="requires_attention",
        ai_summary="振動値の上昇を確認しました。",
        ai_analysis="閾値を超える測定値があります。",
        recommendation="設備を点検してください。",
        report_text="振動分析レポート本文",
        ai_model="test-chat-model",
        prompt_version="v1",
        chart_path=None,
        pdf_path=None,
        pdf_generated_at=None,
        created_at=now,
        updated_at=now,
    )
    anomaly = SimpleNamespace(
        row_number=4,
        measured_at="2026-09-01T10:00:02+09:00",
        value=3.0,
        threshold=2.0,
        excess_value=1.0,
    )
    analysis_dict = {
        "record_count": 3,
        "minimum_value": 1.0,
        "maximum_value": 3.0,
        "average_value": 2.0,
        "median_value": 2.0,
        "standard_deviation": 0.816,
        "threshold_value": 2.0,
        "anomaly_count": 1,
        "anomaly_rate": 1 / 3,
        "status": "requires_attention",
        "anomalies": [vars(anomaly)],
    }
    analysis_result = Mock()
    analysis_result.to_dict.return_value = analysis_dict
    report_chunk = SimpleNamespace(
        id=uuid.uuid4(),
        embedding_model="test-embedding-model",
    )
    return SimpleNamespace(
        report=report,
        report_chunk=report_chunk,
        analysis_result=analysis_result,
        ai_analysis_text="閾値を超える測定値があります。",
    )


def install_report_service_mock(
    monkeypatch: pytest.MonkeyPatch,
    *,
    result=None,
    error: Exception | None = None,
):
    """APIが生成するReportServiceをMockへ差し替える。"""
    service = Mock()
    if error is not None:
        service.generate_report.side_effect = error
    else:
        service.generate_report.return_value = result

    factory = Mock(return_value=service)
    monkeypatch.setattr(reports_module, "ReportService", factory)
    return service, factory


def test_generate_report_returns_500_without_development_user(
    api_client: TestClient,
) -> None:
    """開発用ユーザーがない場合は500を返す。"""
    response = api_client.post(
        "/api/v1/reports/generate",
        json={
            "uploaded_file_id": str(uuid.uuid4()),
            "threshold_value": 2.0,
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "開発用ユーザーが登録されていません。"
    )


def test_generate_report_returns_created_response(
    api_client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """正常時に201とレポート生成結果を返す。"""
    user = create_development_user(db_session)
    result = create_generation_result(user.id)
    service, factory = install_report_service_mock(
        monkeypatch,
        result=result,
    )

    response = api_client.post(
        "/api/v1/reports/generate",
        json={
            "uploaded_file_id": str(result.report.uploaded_file_id),
            "threshold_value": 2.0,
            "weather": "晴れ",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "AIレポートを生成しました。"
    assert body["report"]["id"] == str(result.report.id)
    assert body["report"]["created_by"] == str(user.id)
    assert body["analysis"]["anomaly_count"] == 1
    assert body["analysis"]["status"] == "requires_attention"
    assert body["report_chunk_id"] == str(result.report_chunk.id)
    assert body["embedding_model"] == "test-embedding-model"
    assert body["embedding_dimensions"] == 1536
    factory.assert_called_once_with(db_session)
    service.generate_report.assert_called_once_with(
        uploaded_file_id=result.report.uploaded_file_id,
        created_by=user.id,
        threshold_value=2.0,
        weather="晴れ",
    )


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (ReportSourceFileNotFoundError("管理情報なし"), 404),
        (ReportPhysicalFileNotFoundError("物理CSVなし"), 404),
        (ReportAlreadyExistsError("生成済み"), 409),
        (ReportDatabaseError("DB登録失敗"), 500),
        (ReportGenerationError("AI処理失敗"), 502),
    ],
)
def test_generate_report_maps_service_errors_to_http_status(
    api_client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    expected_status: int,
) -> None:
    """Service例外を所定のHTTP Statusへ変換する。"""
    create_development_user(db_session)
    install_report_service_mock(monkeypatch, error=error)

    response = api_client.post(
        "/api/v1/reports/generate",
        json={
            "uploaded_file_id": str(uuid.uuid4()),
            "threshold_value": 2.0,
        },
    )

    assert response.status_code == expected_status
    assert response.json()["detail"] == str(error)


@pytest.mark.parametrize(
    "payload",
    [
        {"uploaded_file_id": str(uuid.uuid4()), "threshold_value": 0},
        {"uploaded_file_id": str(uuid.uuid4()), "threshold_value": -1},
        {"uploaded_file_id": "not-a-uuid", "threshold_value": 2.0},
        {"uploaded_file_id": str(uuid.uuid4())},
        {
            "uploaded_file_id": str(uuid.uuid4()),
            "threshold_value": 2.0,
            "weather": "晴" * 101,
        },
    ],
)
def test_generate_report_rejects_invalid_request(
    api_client: TestClient,
    payload: dict,
) -> None:
    """不正なRequestでは422を返す。"""
    response = api_client.post(
        "/api/v1/reports/generate",
        json=payload,
    )

    assert response.status_code == 422
