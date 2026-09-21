import hashlib
import uuid
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.src.exceptions.report_exceptions import (
    ReportAlreadyExistsError,
    ReportDatabaseError,
    ReportGenerationError,
    ReportSourceFileNotFoundError,
)
from backend.src.repositories.uploaded_file_repository import UploadedFileRepository
from backend.src.repositories.user_repository import UserRepository
from backend.src.services.csv_service import CsvReadError
from backend.src.services.report_service import ReportService


def create_user(db_session: Session):
    return UserRepository(db_session).create(
        login_id=f"report-service-{uuid.uuid4().hex}",
        password_hash="hashed-password",
        display_name="ReportServiceテストユーザー",
    )


def create_uploaded_file(db_session: Session):
    user = create_user(db_session)
    stored_filename = f"{uuid.uuid4()}.csv"
    uploaded_file = UploadedFileRepository(db_session).create(
        uploaded_by=user.id,
        equipment_id="MOTOR-001",
        original_filename="measurement.csv",
        stored_filename=stored_filename,
        file_path=f"data/uploads/{stored_filename}",
        file_size=128,
        checksum=hashlib.sha256(uuid.uuid4().bytes).hexdigest(),
        mime_type="text/csv",
        status="uploaded",
    )
    return user, uploaded_file


def create_service(db_session: Session) -> ReportService:
    service = ReportService(
        session=db_session,
        csv_service=Mock(),
        analysis_service=Mock(),
        azure_openai_service=Mock(),
    )
    service._analysis_graph = Mock()
    return service


def test_generate_report_returns_graph_result(db_session: Session) -> None:
    service = create_service(db_session)
    report = Mock()
    report_chunk = Mock()
    analysis_result = Mock()
    service._analysis_graph.invoke.return_value = {
        "report": report,
        "report_chunk": report_chunk,
        "analysis_result": analysis_result,
        "ai_analysis_text": "AI分析結果",
    }
    db_session.refresh = Mock()

    result = service.generate_report(
        uploaded_file_id=uuid.uuid4(),
        created_by=uuid.uuid4(),
        threshold_value=2.0,
        weather="晴れ",
    )

    assert result.report is report
    assert result.report_chunk is report_chunk
    assert result.analysis_result is analysis_result
    assert result.ai_analysis_text == "AI分析結果"
    service._analysis_graph.invoke.assert_called_once()
    graph_input = service._analysis_graph.invoke.call_args.args[0]
    assert graph_input["threshold_value"] == 2.0
    assert graph_input["weather"] == "晴れ"
    assert db_session.refresh.call_count == 2


def test_source_file_error_is_rolled_back_and_reraised(
    db_session: Session,
) -> None:
    service = create_service(db_session)
    service._analysis_graph.invoke.side_effect = ReportSourceFileNotFoundError(
        "source not found"
    )
    db_session.rollback = Mock()

    with pytest.raises(ReportSourceFileNotFoundError):
        service.generate_report(uuid.uuid4(), uuid.uuid4(), 2.0)

    db_session.rollback.assert_called_once_with()


def test_already_exists_error_is_rolled_back_and_reraised(
    db_session: Session,
) -> None:
    service = create_service(db_session)
    service._analysis_graph.invoke.side_effect = ReportAlreadyExistsError(
        "already exists"
    )
    db_session.rollback = Mock()

    with pytest.raises(ReportAlreadyExistsError):
        service.generate_report(uuid.uuid4(), uuid.uuid4(), 2.0)

    db_session.rollback.assert_called_once_with()


def test_csv_error_sets_uploaded_file_to_failed(
    db_session: Session,
) -> None:
    user, uploaded_file = create_uploaded_file(db_session)
    db_session.commit()

    service = create_service(db_session)
    service._analysis_graph.invoke.side_effect = CsvReadError("CSV読込失敗")

    with pytest.raises(ReportGenerationError) as exc_info:
        service.generate_report(uploaded_file.id, user.id, 2.0)

    db_session.refresh(uploaded_file)
    assert uploaded_file.status == "failed"
    assert uploaded_file.error_code == "CsvReadError"
    assert uploaded_file.error_message == "CSV読込失敗"
    assert isinstance(exc_info.value.__cause__, CsvReadError)


def test_integrity_error_sets_failure_status_and_raises_database_error(
    db_session: Session,
) -> None:
    user, uploaded_file = create_uploaded_file(db_session)
    db_session.commit()

    service = create_service(db_session)
    service._analysis_graph.invoke.side_effect = IntegrityError(
        statement="INSERT",
        params={},
        orig=Exception("constraint error"),
    )

    with pytest.raises(ReportDatabaseError):
        service.generate_report(uploaded_file.id, user.id, 2.0)

    db_session.refresh(uploaded_file)
    assert uploaded_file.status == "failed"
    assert uploaded_file.error_code == "IntegrityError"
    assert "DB登録に失敗" in uploaded_file.error_message


def test_unexpected_error_sets_failure_status_and_preserves_cause(
    db_session: Session,
) -> None:
    user, uploaded_file = create_uploaded_file(db_session)
    db_session.commit()

    service = create_service(db_session)
    service._analysis_graph.invoke.side_effect = RuntimeError("unexpected")

    with pytest.raises(ReportGenerationError) as exc_info:
        service.generate_report(uploaded_file.id, user.id, 2.0)

    db_session.refresh(uploaded_file)
    assert uploaded_file.status == "failed"
    assert uploaded_file.error_code == "RuntimeError"
    assert uploaded_file.error_message == "unexpected"
    assert isinstance(exc_info.value.__cause__, RuntimeError)


def test_failure_status_is_safely_truncated(db_session: Session) -> None:
    _, uploaded_file = create_uploaded_file(db_session)
    service = create_service(db_session)

    service._save_failure_status(
        uploaded_file_id=uploaded_file.id,
        error_code="E" * 150,
        error_message="M" * 2500,
    )

    db_session.refresh(uploaded_file)
    assert uploaded_file.status == "failed"
    assert len(uploaded_file.error_code) == 100
    assert len(uploaded_file.error_message) == 2000


def test_failure_status_ignores_unknown_uploaded_file(
    db_session: Session,
) -> None:
    service = create_service(db_session)

    service._save_failure_status(
        uploaded_file_id=uuid.uuid4(),
        error_code="Unknown",
        error_message="not found",
    )
