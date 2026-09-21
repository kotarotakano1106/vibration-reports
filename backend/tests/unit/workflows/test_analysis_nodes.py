import uuid
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import backend.src.workflows.nodes.analysis_nodes as analysis_module
from backend.src.exceptions.report_exceptions import (
    ReportAlreadyExistsError,
    ReportPhysicalFileNotFoundError,
    ReportSourceFileNotFoundError,
)
from backend.src.workflows.nodes.analysis_nodes import AnalysisNodes


def make_nodes() -> AnalysisNodes:
    """依存関係をMock化したAnalysisNodesを作成する。"""
    nodes = AnalysisNodes(
        session=Mock(),
        csv_service=Mock(),
        analysis_service=Mock(),
        azure_openai_service=Mock(),
    )
    nodes._file_repository = Mock()
    nodes._report_repository = Mock()
    return nodes


def make_uploaded_file(**overrides):
    """分析Node用のCSV管理情報を作成する。"""
    uploaded_file = SimpleNamespace(
        id=uuid.uuid4(),
        file_path="data/uploads/measurement.csv",
        encoding="UTF-8",
        equipment_id="MOTOR-001",
        measurement_date=date(2026, 9, 1),
    )
    for name, value in overrides.items():
        setattr(uploaded_file, name, value)
    return uploaded_file


def make_analysis_result():
    """AI分析Nodeへ渡す振動分析結果を作成する。"""
    return SimpleNamespace(
        record_count=3,
        minimum_value=1.0,
        maximum_value=3.0,
        average_value=2.0,
        median_value=2.0,
        standard_deviation=0.816,
        threshold_value=2.5,
        anomaly_count=1,
    )


def test_load_uploaded_file_returns_related_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CSV管理情報と物理ファイル情報をStateへ追加する。"""
    nodes = make_nodes()
    csv_path = tmp_path / "data" / "uploads" / "measurement.csv"
    csv_path.parent.mkdir(parents=True)
    csv_path.write_text("vibration_value\n1.0\n", encoding="utf-8")
    uploaded_file = make_uploaded_file()
    nodes._file_repository.get_by_id.return_value = uploaded_file
    monkeypatch.setattr(analysis_module, "PROJECT_ROOT", tmp_path)

    result = nodes.load_uploaded_file(
        {"uploaded_file_id": uploaded_file.id}
    )

    assert result == {
        "uploaded_file": uploaded_file,
        "csv_path": str(csv_path),
        "encoding": "UTF-8",
        "equipment_id": "MOTOR-001",
        "measurement_date": date(2026, 9, 1),
    }
    nodes._file_repository.get_by_id.assert_called_once_with(uploaded_file.id)


def test_load_uploaded_file_accepts_absolute_path(tmp_path: Path) -> None:
    """絶対パスのCSVをそのまま使用する。"""
    nodes = make_nodes()
    csv_path = tmp_path / "measurement.csv"
    csv_path.write_text("vibration_value\n1.0\n", encoding="utf-8")
    uploaded_file = make_uploaded_file(file_path=str(csv_path))
    nodes._file_repository.get_by_id.return_value = uploaded_file

    result = nodes.load_uploaded_file(
        {"uploaded_file_id": uploaded_file.id}
    )

    assert result["csv_path"] == str(csv_path)


def test_load_uploaded_file_rejects_unknown_record() -> None:
    """CSV管理情報が存在しない場合は専用例外を送出する。"""
    nodes = make_nodes()
    uploaded_file_id = uuid.uuid4()
    nodes._file_repository.get_by_id.return_value = None

    with pytest.raises(ReportSourceFileNotFoundError):
        nodes.load_uploaded_file({"uploaded_file_id": uploaded_file_id})


@pytest.mark.parametrize("path_is_directory", [False, True])
def test_load_uploaded_file_rejects_invalid_physical_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    path_is_directory: bool,
) -> None:
    """物理CSV不在またはディレクトリの場合は専用例外を送出する。"""
    nodes = make_nodes()
    csv_path = tmp_path / "data" / "uploads" / "measurement.csv"
    if path_is_directory:
        csv_path.mkdir(parents=True)
    uploaded_file = make_uploaded_file()
    nodes._file_repository.get_by_id.return_value = uploaded_file
    monkeypatch.setattr(analysis_module, "PROJECT_ROOT", tmp_path)

    with pytest.raises(ReportPhysicalFileNotFoundError):
        nodes.load_uploaded_file({"uploaded_file_id": uploaded_file.id})


def test_check_existing_report_returns_empty_update() -> None:
    """未作成の場合はState更新なしで次へ進む。"""
    nodes = make_nodes()
    uploaded_file = make_uploaded_file()
    nodes._report_repository.get_by_uploaded_file_id.return_value = None

    result = nodes.check_existing_report({"uploaded_file": uploaded_file})

    assert result == {}
    nodes._report_repository.get_by_uploaded_file_id.assert_called_once_with(
        uploaded_file.id
    )


def test_check_existing_report_rejects_duplicate() -> None:
    """同一CSVのReportが存在する場合は重複例外を送出する。"""
    nodes = make_nodes()
    uploaded_file = make_uploaded_file()
    existing_report = SimpleNamespace(id=uuid.uuid4())
    nodes._report_repository.get_by_uploaded_file_id.return_value = (
        existing_report
    )

    with pytest.raises(ReportAlreadyExistsError) as exc_info:
        nodes.check_existing_report({"uploaded_file": uploaded_file})

    assert str(existing_report.id) in str(exc_info.value)


def test_mark_processing_updates_status() -> None:
    """CSV管理情報をprocessingへ更新する。"""
    nodes = make_nodes()
    uploaded_file = make_uploaded_file()
    updated_file = make_uploaded_file()
    nodes._file_repository.update_status.return_value = updated_file

    result = nodes.mark_processing({"uploaded_file": uploaded_file})

    assert result == {"uploaded_file": updated_file}
    nodes._file_repository.update_status.assert_called_once_with(
        uploaded_file,
        status="processing",
        error_code=None,
        error_message=None,
    )


def test_load_and_validate_csv_passes_path_and_encoding() -> None:
    """CSV ServiceへPathと文字コードを渡す。"""
    nodes = make_nodes()
    dataframe = Mock()
    nodes._csv_service.load.return_value = dataframe

    result = nodes.load_and_validate_csv(
        {"csv_path": "data/uploads/measurement.csv", "encoding": "UTF-8"}
    )

    assert result == {"dataframe": dataframe}
    nodes._csv_service.load.assert_called_once_with(
        Path("data/uploads/measurement.csv"),
        encoding="UTF-8",
    )


def test_analyze_vibration_passes_dataframe_and_threshold() -> None:
    """分析ServiceへDataFrameと閾値を渡す。"""
    nodes = make_nodes()
    dataframe = Mock()
    analysis_result = make_analysis_result()
    nodes._analysis_service.analyze.return_value = analysis_result

    result = nodes.analyze_vibration(
        {"dataframe": dataframe, "threshold_value": 2.5}
    )

    assert result == {"analysis_result": analysis_result}
    nodes._analysis_service.analyze.assert_called_once_with(
        dataframe,
        threshold_value=2.5,
    )


def test_generate_ai_analysis_passes_statistics() -> None:
    """分析結果の統計値をAzure OpenAI Serviceへ渡す。"""
    nodes = make_nodes()
    analysis_result = make_analysis_result()
    nodes._azure_openai_service.generate_vibration_analysis.return_value = (
        "AI分析結果"
    )

    result = nodes.generate_ai_analysis(
        {
            "analysis_result": analysis_result,
            "equipment_id": "MOTOR-001",
            "measurement_date": date(2026, 9, 1),
        }
    )

    assert result == {"ai_analysis_text": "AI分析結果"}
    nodes._azure_openai_service.generate_vibration_analysis.assert_called_once_with(
        equipment_id="MOTOR-001",
        measurement_date=date(2026, 9, 1),
        record_count=3,
        minimum_value=1.0,
        maximum_value=3.0,
        average_value=2.0,
        median_value=2.0,
        standard_deviation=0.816,
        threshold_value=2.5,
        anomaly_count=1,
    )


def test_resolve_csv_path_uses_project_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """相対パスをProject Root配下の絶対パスへ変換する。"""
    monkeypatch.setattr(analysis_module, "PROJECT_ROOT", tmp_path)

    result = AnalysisNodes._resolve_csv_path("data/uploads/test.csv")

    assert result == tmp_path / "data" / "uploads" / "test.csv"
