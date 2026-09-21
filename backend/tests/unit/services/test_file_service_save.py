import hashlib
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError

import backend.src.services.file_service as file_service_module
from backend.src.services.file_service import (
    FileAlreadyExistsError,
    FileDatabaseError,
    FileSaveResult,
    FileService,
)


@pytest.fixture
def session() -> Mock:
    """テスト用DB Sessionを作成する。"""

    return Mock()


@pytest.fixture
def service(
    tmp_path: Path,
    session: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> FileService:
    """RepositoryをMock化したFileServiceを作成する。"""

    monkeypatch.setattr(
        file_service_module,
        "PROJECT_ROOT",
        tmp_path,
    )

    instance = FileService(
        session=session,
        upload_directory=tmp_path / "uploads",
        max_file_size=1024,
    )
    instance._repository = Mock()

    return instance


def test_save_csv_saves_file_and_database_record(
    service: FileService,
    session: Mock,
) -> None:
    """CSVを保存し、管理情報をDBへ登録する。"""

    file_content = (
        b"measured_at,vibration_value\n"
        b"2026-09-01T10:00:00+09:00,1.5\n"
    )
    uploaded_by = "00000000-0000-0000-0000-000000000001"
    created_record = SimpleNamespace(
        id="00000000-0000-0000-0000-000000000002",
    )

    service._repository.get_by_checksum.return_value = None
    service._repository.create.return_value = created_record

    result = service.save_csv(
        file_content=file_content,
        original_filename="measurement.csv",
        uploaded_by=uploaded_by,
        equipment_id=" MOTOR-001 ",
        measurement_date=date(2026, 9, 1),
        mime_type="TEXT/CSV; charset=UTF-8",
        encoding="UTF-8",
    )

    assert isinstance(result, FileSaveResult)
    assert result.uploaded_file is created_record
    assert result.is_duplicate is False
    assert result.absolute_path.exists()
    assert result.absolute_path.read_bytes() == file_content
    assert result.absolute_path.suffix == ".csv"

    expected_checksum = hashlib.sha256(
        file_content
    ).hexdigest()

    service._repository.get_by_checksum.assert_called_once_with(
        expected_checksum
    )
    service._repository.create.assert_called_once()

    create_arguments = (
        service._repository.create.call_args.kwargs
    )

    assert create_arguments["equipment_id"] == "MOTOR-001"
    assert create_arguments["original_filename"] == (
        "measurement.csv"
    )
    assert create_arguments["file_size"] == len(file_content)
    assert create_arguments["checksum"] == expected_checksum
    assert create_arguments["mime_type"] == "text/csv"
    assert create_arguments["encoding"] == "UTF-8"
    assert create_arguments["status"] == "uploaded"

    UUID(create_arguments["stored_filename"].removesuffix(".csv"))

    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(created_record)
    session.rollback.assert_not_called()


def test_save_csv_returns_existing_record_for_duplicate(
    service: FileService,
    session: Mock,
    tmp_path: Path,
) -> None:
    """重複ファイルでは既存レコードを返す。"""

    file_content = b"same-content"
    existing_record = SimpleNamespace(
        id="existing-id",
        file_path="data/uploads/existing.csv",
    )

    service._repository.get_by_checksum.return_value = (
        existing_record
    )

    result = service.save_csv(
        file_content=file_content,
        original_filename="measurement.csv",
        uploaded_by="user-id",
        equipment_id="MOTOR-001",
    )

    assert result.uploaded_file is existing_record
    assert result.is_duplicate is True
    assert result.absolute_path == (
        tmp_path / "data/uploads/existing.csv"
    )

    service._repository.create.assert_not_called()
    session.commit.assert_not_called()
    session.refresh.assert_not_called()
    session.rollback.assert_not_called()


def test_save_csv_rejects_duplicate_when_requested(
    service: FileService,
    session: Mock,
) -> None:
    """重複拒否指定では専用例外を送出する。"""

    existing_record = SimpleNamespace(
        id="existing-id",
        file_path="data/uploads/existing.csv",
    )
    service._repository.get_by_checksum.return_value = (
        existing_record
    )

    with pytest.raises(FileAlreadyExistsError):
        service.save_csv(
            file_content=b"same-content",
            original_filename="measurement.csv",
            uploaded_by="user-id",
            equipment_id="MOTOR-001",
            reject_duplicate=True,
        )

    service._repository.create.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_save_csv_rolls_back_and_removes_file_on_integrity_error(
    service: FileService,
    session: Mock,
) -> None:
    """DB制約違反時にRollbackし、保存済みファイルを削除する。"""

    service._repository.get_by_checksum.return_value = None
    service._repository.create.side_effect = IntegrityError(
        statement="INSERT",
        params={},
        orig=Exception("constraint error"),
    )

    with pytest.raises(FileDatabaseError):
        service.save_csv(
            file_content=b"header\nvalue\n",
            original_filename="measurement.csv",
            uploaded_by="user-id",
            equipment_id="MOTOR-001",
        )

    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()

    upload_directory = service._upload_directory

    remaining_files = list(
        upload_directory.glob("*")
    )

    assert remaining_files == []


def test_save_csv_rolls_back_and_removes_file_on_unexpected_error(
    service: FileService,
    session: Mock,
) -> None:
    """想定外のDBエラーでもRollbackとファイル削除を行う。"""

    service._repository.get_by_checksum.return_value = None
    service._repository.create.side_effect = RuntimeError(
        "unexpected database error"
    )

    with pytest.raises(
        RuntimeError,
        match="unexpected database error",
    ):
        service.save_csv(
            file_content=b"header\nvalue\n",
            original_filename="measurement.csv",
            uploaded_by="user-id",
            equipment_id="MOTOR-001",
        )

    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()

    remaining_files = list(
        service._upload_directory.glob("*")
    )

    assert remaining_files == []
