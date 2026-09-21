import uuid
from datetime import UTC, date, datetime
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import backend.src.services.report_pdf_service as pdf_module
from backend.src.services.report_pdf_service import (
    ReportPdfNotFoundError,
    ReportPdfService,
    ReportPdfSourceFileError,
)


def make_report(**overrides):
    """PDF生成に必要なReport属性を持つテストデータを作成する。"""
    report = SimpleNamespace(
        id=uuid.uuid4(),
        uploaded_file_id=uuid.uuid4(),
        equipment_id="MOTOR-001",
        measurement_date=date(2026, 9, 1),
        weather="晴れ",
        title="振動分析レポート",
        record_count=3,
        minimum_value=1.0,
        maximum_value=3.0,
        average_value=2.0,
        threshold_value=2.5,
        anomaly_count=1,
        anomaly_details=[
            {
                "row_number": 4,
                "measured_at": "2026-09-01T10:00:02+09:00",
                "value": 3.0,
                "threshold": 2.5,
                "excess_value": 0.5,
            }
        ],
        status="requires_attention",
        ai_summary="振動値の上昇を確認しました。",
        ai_analysis="閾値を超える測定値が1件あります。",
        recommendation="設備を点検してください。",
        created_at=datetime(2026, 9, 1, 12, 0, tzinfo=UTC),
    )
    for name, value in overrides.items():
        setattr(report, name, value)
    return report


def make_uploaded_file(**overrides):
    """PDF生成に必要なUploadedFile属性を持つテストデータを作成する。"""
    uploaded_file = SimpleNamespace(
        id=uuid.uuid4(),
        original_filename="measurement.csv",
        file_path="data/uploads/measurement.csv",
        encoding="UTF-8",
    )
    for name, value in overrides.items():
        setattr(uploaded_file, name, value)
    return uploaded_file


def make_service() -> ReportPdfService:
    """RepositoryをMock化したReportPdfServiceを作成する。"""
    service = ReportPdfService(Mock())
    service._report_repository = Mock()
    service._file_repository = Mock()
    return service


def test_generate_returns_pdf_and_safe_filename(tmp_path, monkeypatch) -> None:
    """ReportとCSVからPDFを生成し、安全なファイル名を返す。"""
    service = make_service()
    report = make_report(equipment_id="MOTOR 001/A")
    csv_path = tmp_path / "data" / "uploads" / "measurement.csv"
    csv_path.parent.mkdir(parents=True)
    csv_path.write_text(
        "measured_at,vibration_value\n"
        "2026-09-01T10:00:00+09:00,1.0\n"
        "2026-09-01T10:00:01+09:00,2.0\n"
        "2026-09-01T10:00:02+09:00,3.0\n",
        encoding="utf-8",
    )
    uploaded_file = make_uploaded_file()
    service._report_repository.get_by_id.return_value = report
    service._file_repository.get_by_id.return_value = uploaded_file
    monkeypatch.setattr(pdf_module, "PROJECT_ROOT", tmp_path)

    pdf_bytes, filename = service.generate(report.id)

    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 1000
    assert filename == "vibration-report_MOTOR_001_A_2026-09-01.pdf"


def test_generate_uses_date_unset_in_filename(tmp_path, monkeypatch) -> None:
    """測定日未設定の場合はdate-unsetをファイル名へ使用する。"""
    service = make_service()
    report = make_report(measurement_date=None)
    uploaded_file = make_uploaded_file(file_path="measurement.csv")
    (tmp_path / "measurement.csv").write_text(
        "vibration_value\n1.0\n",
        encoding="utf-8",
    )
    service._report_repository.get_by_id.return_value = report
    service._file_repository.get_by_id.return_value = uploaded_file
    monkeypatch.setattr(pdf_module, "PROJECT_ROOT", tmp_path)
    service._build_pdf = Mock(
        side_effect=lambda buffer, *_: buffer.write(b"%PDF-mock")
    )

    pdf_bytes, filename = service.generate(report.id)

    assert pdf_bytes == b"%PDF-mock"
    assert filename == "vibration-report_MOTOR-001_date-unset.pdf"


def test_generate_rejects_unknown_report() -> None:
    """存在しないReportでは専用例外を送出する。"""
    service = make_service()
    service._report_repository.get_by_id.return_value = None
    report_id = uuid.uuid4()

    with pytest.raises(ReportPdfNotFoundError):
        service.generate(report_id)

    service._file_repository.get_by_id.assert_not_called()


def test_generate_rejects_missing_uploaded_file() -> None:
    """対応するCSV管理情報がない場合は専用例外を送出する。"""
    service = make_service()
    report = make_report()
    service._report_repository.get_by_id.return_value = report
    service._file_repository.get_by_id.return_value = None

    with pytest.raises(ReportPdfSourceFileError):
        service.generate(report.id)


def test_load_values_reads_relative_csv(tmp_path, monkeypatch) -> None:
    """相対パスのCSVから振動値を読み込む。"""
    csv_path = tmp_path / "data" / "uploads" / "measurement.csv"
    csv_path.parent.mkdir(parents=True)
    csv_path.write_text(
        "measured_at,vibration_value\n"
        "2026-09-01T10:00:00+09:00,1.25\n"
        "2026-09-01T10:00:01+09:00,2.50\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(pdf_module, "PROJECT_ROOT", tmp_path)

    result = ReportPdfService._load_values(
        "data/uploads/measurement.csv",
        "UTF-8",
    )

    assert result == [1.25, 2.5]


def test_load_values_reads_absolute_csv(tmp_path) -> None:
    """絶対パスのCSVから振動値を読み込む。"""
    csv_path = tmp_path / "measurement.csv"
    csv_path.write_text("vibration_value\n3.5\n", encoding="utf-8")

    assert ReportPdfService._load_values(csv_path, None) == [3.5]


def test_load_values_rejects_missing_file(tmp_path) -> None:
    """CSV実ファイルがない場合は専用例外を送出する。"""
    with pytest.raises(ReportPdfSourceFileError):
        ReportPdfService._load_values(tmp_path / "missing.csv", "UTF-8")


@pytest.mark.parametrize(
    "csv_text",
    [
        "other_column\n1.0\n",
        "vibration_value\nnot-number\n",
    ],
)
def test_load_values_wraps_invalid_csv(tmp_path, csv_text: str) -> None:
    """列不足または数値変換失敗を専用例外へ変換する。"""
    csv_path = tmp_path / "invalid.csv"
    csv_path.write_text(csv_text, encoding="utf-8")

    with pytest.raises(ReportPdfSourceFileError) as exc_info:
        ReportPdfService._load_values(csv_path, "UTF-8")

    assert exc_info.value.__cause__ is not None


def test_load_values_wraps_encoding_error(tmp_path) -> None:
    """文字コード不一致を専用例外へ変換する。"""
    csv_path = tmp_path / "shift-jis.csv"
    csv_path.write_bytes("振動値".encode("shift_jis"))

    with pytest.raises(ReportPdfSourceFileError):
        ReportPdfService._load_values(csv_path, "UTF-8")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, "AI分析はありません。"),
        ("# 見出し\n本文", "見出し<br/>本文"),
        ("A & B < C", "A &amp; B &lt; C"),
        ("1行目<br>2行目", "1行目<br/>2行目"),
    ],
)
def test_paragraph_text_normalizes_and_escapes(value, expected: str) -> None:
    """PDF用本文を正規化しXML特殊文字をEscapeする。"""
    assert ReportPdfService._paragraph_text(value) == expected


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("requires_attention", "要確認"),
        ("warning", "注意"),
        ("normal", "正常"),
        ("custom", "custom"),
        (None, "未設定"),
    ],
)
def test_status_label(status, expected: str) -> None:
    """Statusを日本語表示へ変換する。"""
    assert ReportPdfService._status_label(status) == expected


def test_date_text_formats_value() -> None:
    """日付を日本語形式へ変換する。"""
    assert ReportPdfService._date_text(date(2026, 9, 1)) == "2026年09月01日"
    assert ReportPdfService._date_text(None) == "未設定"


def test_datetime_text_formats_value() -> None:
    """日時を日本語形式へ変換する。"""
    value = datetime(2026, 9, 1, 12, 34, tzinfo=UTC)

    assert "2026年09月01日" in ReportPdfService._datetime_text(value)
    assert ReportPdfService._datetime_text(None) == "未設定"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, "-"),
        ("", "-"),
        ("not-a-date", "not-a-date"),
    ],
)
def test_anomaly_time_handles_empty_and_invalid_values(value, expected: str) -> None:
    """異常時刻の空値と不正値を安全に表示する。"""
    assert ReportPdfService._anomaly_time(value) == expected


def test_anomaly_time_formats_iso_datetime() -> None:
    """ISO形式日時を時刻表示へ変換する。"""
    result = ReportPdfService._anomaly_time(
        "2026-09-01T10:20:30+09:00"
    )

    assert result.endswith(":20:30") or result == "10:20:30"


def test_build_pdf_supports_empty_optional_sections() -> None:
    """Optional項目が空でもPDFを生成できる。"""
    service = make_service()
    report = make_report(
        weather=None,
        threshold_value=None,
        anomaly_count=0,
        anomaly_details=[],
        ai_summary=None,
        ai_analysis=None,
        recommendation=None,
        status="normal",
    )
    uploaded_file = make_uploaded_file()
    buffer = BytesIO()

    service._build_pdf(buffer, report, uploaded_file, [])

    assert buffer.getvalue().startswith(b"%PDF-")
