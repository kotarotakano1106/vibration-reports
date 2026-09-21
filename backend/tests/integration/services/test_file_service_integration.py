import hashlib
import uuid
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

import backend.src.services.file_service as file_service_module
from backend.src.models.uploaded_file import UploadedFile
from backend.src.repositories.user_repository import UserRepository
from backend.src.services.file_service import (
    FileAlreadyExistsError,
    FileService,
)


def unique_login_id() -> str:
    """テスト用の一意なログインIDを生成する。"""
    return f"file-service-user-{uuid.uuid4().hex}"


def create_test_user(db_session: Session):
    """CSV登録に必要なテストユーザーを作成する。"""
    return UserRepository(db_session).create(
        login_id=unique_login_id(),
        password_hash="hashed-password",
        display_name="FileService結合テストユーザー",
    )


@pytest.fixture
def upload_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """プロジェクト外へ影響しない一時保存先を作成する。"""
    monkeypatch.setattr(
        file_service_module,
        "PROJECT_ROOT",
        tmp_path,
    )
    return tmp_path / "data" / "uploads"


@pytest.fixture
def file_service(
    db_session: Session,
    upload_directory: Path,
) -> FileService:
    """テストDBと一時保存先を使うFileServiceを作成する。"""
    return FileService(
        session=db_session,
        upload_directory=upload_directory,
        max_file_size=1024 * 1024,
    )


def test_save_csv_persists_file_and_database_record(
    db_session: Session,
    file_service: FileService,
) -> None:
    """CSVファイルと管理情報を同時に保存できる。"""
    user = create_test_user(db_session)
    file_content = (
        b"measured_at,vibration_value\n"
        b"2026-09-01T10:00:00+09:00,1.5\n"
    )

    result = file_service.save_csv(
        file_content=file_content,
        original_filename="measurement.csv",
        uploaded_by=user.id,
        equipment_id="MOTOR-001",
        mime_type="text/csv; charset=UTF-8",
        encoding="UTF-8",
    )

    assert result.is_duplicate is False
    assert result.absolute_path.exists()
    assert result.absolute_path.read_bytes() == file_content

    stored = db_session.scalar(
        select(UploadedFile).where(
            UploadedFile.id == result.uploaded_file.id
        )
    )

    assert stored is not None
    assert stored.original_filename == "measurement.csv"
    assert stored.equipment_id == "MOTOR-001"
    assert stored.file_size == len(file_content)
    assert stored.mime_type == "text/csv"
    assert stored.encoding == "UTF-8"
    assert stored.status == "uploaded"
    assert stored.checksum == hashlib.sha256(file_content).hexdigest()
    assert stored.file_path.startswith("data/uploads/")


def test_save_csv_returns_existing_record_for_duplicate(
    db_session: Session,
    file_service: FileService,
) -> None:
    """同一内容の再登録では既存レコードを返す。"""
    user = create_test_user(db_session)
    file_content = b"measured_at,vibration_value\n2026-09-01,1.0\n"

    first = file_service.save_csv(
        file_content=file_content,
        original_filename="first.csv",
        uploaded_by=user.id,
        equipment_id="MOTOR-001",
    )
    second = file_service.save_csv(
        file_content=file_content,
        original_filename="second.csv",
        uploaded_by=user.id,
        equipment_id="MOTOR-001",
    )

    assert first.is_duplicate is False
    assert second.is_duplicate is True
    assert second.uploaded_file.id == first.uploaded_file.id
    assert second.absolute_path == first.absolute_path

    matching_count = len(
        db_session.scalars(
            select(UploadedFile).where(
                UploadedFile.checksum
                == hashlib.sha256(file_content).hexdigest()
            )
        ).all()
    )
    assert matching_count == 1


def test_save_csv_rejects_duplicate_when_requested(
    db_session: Session,
    file_service: FileService,
) -> None:
    """重複拒否指定では既存CSVの再登録を拒否する。"""
    user = create_test_user(db_session)
    file_content = b"measured_at,vibration_value\n2026-09-01,2.0\n"

    first = file_service.save_csv(
        file_content=file_content,
        original_filename="first.csv",
        uploaded_by=user.id,
        equipment_id="MOTOR-001",
    )

    with pytest.raises(FileAlreadyExistsError):
        file_service.save_csv(
            file_content=file_content,
            original_filename="duplicate.csv",
            uploaded_by=user.id,
            equipment_id="MOTOR-001",
            reject_duplicate=True,
        )

    assert first.absolute_path.exists()


def test_saved_file_is_confined_to_temporary_directory(
    db_session: Session,
    file_service: FileService,
    upload_directory: Path,
) -> None:
    """テスト中の保存先が一時ディレクトリ配下に限定される。"""
    user = create_test_user(db_session)

    result = file_service.save_csv(
        file_content=b"measured_at,vibration_value\n2026-09-01,3.0\n",
        original_filename="safe.csv",
        uploaded_by=user.id,
        equipment_id="MOTOR-001",
    )

    assert result.absolute_path.parent == upload_directory
    assert result.absolute_path.is_relative_to(upload_directory)
