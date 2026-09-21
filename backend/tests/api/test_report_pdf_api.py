import uuid
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import backend.src.api.v1.reports as reports_module
from backend.src.services.report_pdf_service import (
    ReportPdfNotFoundError,
    ReportPdfServiceError,
)


def install_pdf_service_mock(
    monkeypatch: pytest.MonkeyPatch,
    *,
    pdf_bytes: bytes | None = None,
    filename: str = "vibration-report.pdf",
    error: Exception | None = None,
) -> tuple[Mock, Mock]:
    """APIが生成するReportPdfServiceをMockへ差し替える。"""
    service = Mock()

    if error is not None:
        service.generate.side_effect = error
    else:
        service.generate.return_value = (
            pdf_bytes or b"%PDF-1.4\nmock-pdf\n%%EOF",
            filename,
        )

    factory = Mock(return_value=service)
    monkeypatch.setattr(
        reports_module,
        "ReportPdfService",
        factory,
    )

    return service, factory


def test_download_report_pdf_returns_pdf_response(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """正常時にPDF本体とダウンロード用Headerを返す。"""
    report_id = uuid.uuid4()
    pdf_bytes = b"%PDF-1.4\nmock-vibration-report\n%%EOF"
    filename = "vibration-report.pdf"
    service, factory = install_pdf_service_mock(
        monkeypatch,
        pdf_bytes=pdf_bytes,
        filename=filename,
    )

    response = api_client.get(
        f"/api/v1/reports/{report_id}/pdf"
    )

    assert response.status_code == 200
    assert response.content == pdf_bytes
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == (
        f'attachment; filename="{filename}"'
    )
    assert response.headers["cache-control"] == "no-store"
    factory.assert_called_once()
    service.generate.assert_called_once_with(report_id)


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_detail"),
    [
        (
            ReportPdfNotFoundError("レポートが存在しません。"),
            404,
            "レポートが存在しません。",
        ),
        (
            ReportPdfServiceError("PDF生成に失敗しました。"),
            500,
            "PDF生成に失敗しました。",
        ),
    ],
)
def test_download_report_pdf_maps_service_errors(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    expected_status: int,
    expected_detail: str,
) -> None:
    """PDF Serviceの例外を所定のHTTP Statusへ変換する。"""
    report_id = uuid.uuid4()
    service, _ = install_pdf_service_mock(
        monkeypatch,
        error=error,
    )

    response = api_client.get(
        f"/api/v1/reports/{report_id}/pdf"
    )

    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail
    service.generate.assert_called_once_with(report_id)


def test_download_report_pdf_rejects_invalid_uuid(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """不正なReport UUIDでは422を返し、Serviceを呼ばない。"""
    service, factory = install_pdf_service_mock(
        monkeypatch,
    )

    response = api_client.get(
        "/api/v1/reports/not-a-uuid/pdf"
    )

    assert response.status_code == 422
    factory.assert_not_called()
    service.generate.assert_not_called()
