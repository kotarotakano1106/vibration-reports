import hashlib
import uuid
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.src.repositories.uploaded_file_repository import (
    UploadedFileRepository,
)
from backend.src.repositories.user_repository import UserRepository


def unique_text(prefix: str) -> str:
    """テストごとに一意な文字列を生成する。"""
    return f"{prefix}-{uuid.uuid4().hex}"


def create_test_user(db_session: Session):
    """Foreign Key用のテストユーザーを作成する。"""
    return UserRepository(db_session).create(
        login_id=unique_text("uploaded-file-user"),
        password_hash="hashed-password",
        display_name="CSV管理情報テストユーザー",
    )


def create_uploaded_file(
    db_session: Session,
    *,
    equipment_id: str = "MOTOR-001",
    stored_filename: str | None = None,
    checksum: str | None = None,
    status: str = "uploaded",
):
    """テスト用CSV管理情報を作成する。"""
    user = create_test_user(db_session)
    repository = UploadedFileRepository(db_session)
    stored_filename = stored_filename or f"{uuid.uuid4()}.csv"
    checksum = checksum or hashlib.sha256(uuid.uuid4().bytes).hexdigest()
    return repository.create(
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
        status=status,
    )


def test_create_and_get_by_id(db_session: Session) -> None:
    repository = UploadedFileRepository(db_session)
    created = create_uploaded_file(db_session)
    found = repository.get_by_id(created.id)
    assert found is not None
    assert found.id == created.id
    assert found.equipment_id == "MOTOR-001"
    assert found.original_filename == "measurement.csv"
    assert found.file_size == 128
    assert found.status == "uploaded"


def test_get_by_stored_filename(db_session: Session) -> None:
    repository = UploadedFileRepository(db_session)
    stored_filename = f"{uuid.uuid4()}.csv"
    created = create_uploaded_file(db_session, stored_filename=stored_filename)
    found = repository.get_by_stored_filename(stored_filename)
    assert found is not None
    assert found.id == created.id


def test_get_by_checksum(db_session: Session) -> None:
    repository = UploadedFileRepository(db_session)
    checksum = hashlib.sha256(b"uploaded-file-checksum-test").hexdigest()
    created = create_uploaded_file(db_session, checksum=checksum)
    found = repository.get_by_checksum(checksum)
    assert found is not None
    assert found.id == created.id
    assert found.checksum == checksum


def test_get_returns_none_for_unknown_values(db_session: Session) -> None:
    repository = UploadedFileRepository(db_session)
    assert repository.get_by_id(uuid.uuid4()) is None
    assert repository.get_by_stored_filename(f"{uuid.uuid4()}.csv") is None
    unknown_checksum = hashlib.sha256(uuid.uuid4().bytes).hexdigest()
    assert repository.get_by_checksum(unknown_checksum) is None


def test_list_by_equipment_id(db_session: Session) -> None:
    repository = UploadedFileRepository(db_session)
    first = create_uploaded_file(db_session, equipment_id="MOTOR-LIST-001")
    second = create_uploaded_file(db_session, equipment_id="MOTOR-LIST-001")
    create_uploaded_file(db_session, equipment_id="MOTOR-OTHER-001")
    result = repository.list_by_equipment_id("MOTOR-LIST-001")
    result_ids = {item.id for item in result}
    assert first.id in result_ids
    assert second.id in result_ids
    assert all(item.equipment_id == "MOTOR-LIST-001" for item in result)


def test_list_by_equipment_id_applies_limit_and_offset(db_session: Session) -> None:
    repository = UploadedFileRepository(db_session)
    base_time = datetime.now().astimezone()
    created_files = []
    for index in range(3):
        item = create_uploaded_file(db_session, equipment_id="MOTOR-PAGING-001")
        item.uploaded_at = base_time + timedelta(minutes=index)
        created_files.append(item)
    db_session.flush()
    first_page = repository.list_by_equipment_id("MOTOR-PAGING-001", limit=2, offset=0)
    second_page = repository.list_by_equipment_id("MOTOR-PAGING-001", limit=2, offset=2)
    assert len(first_page) == 2
    assert len(second_page) == 1
    assert first_page[0].id == created_files[2].id
    assert first_page[1].id == created_files[1].id
    assert second_page[0].id == created_files[0].id


def test_update_status_and_error_information(db_session: Session) -> None:
    repository = UploadedFileRepository(db_session)
    uploaded_file = create_uploaded_file(db_session)
    original_updated_at = uploaded_file.updated_at
    updated = repository.update_status(
        uploaded_file,
        status="failed",
        error_code="CSV_READ_ERROR",
        error_message="CSVの形式を確認してください。",
    )
    assert updated.status == "failed"
    assert updated.error_code == "CSV_READ_ERROR"
    assert updated.error_message == "CSVの形式を確認してください。"
    assert updated.updated_at is not None
    assert updated.updated_at != original_updated_at

def test_stored_filename_must_be_unique(db_session: Session) -> None:
    stored_filename = f"{uuid.uuid4()}.csv"
    create_uploaded_file(db_session, stored_filename=stored_filename)
    with pytest.raises(IntegrityError):
        create_uploaded_file(db_session, stored_filename=stored_filename)
    db_session.rollback()


def test_file_size_must_be_positive(db_session: Session) -> None:
    user = create_test_user(db_session)
    repository = UploadedFileRepository(db_session)
    with pytest.raises(IntegrityError):
        repository.create(
            uploaded_by=user.id,
            equipment_id="MOTOR-001",
            original_filename="invalid-size.csv",
            stored_filename=f"{uuid.uuid4()}.csv",
            file_path="data/uploads/invalid-size.csv",
            file_size=0,
            checksum=hashlib.sha256(b"invalid-size").hexdigest(),
        )
    db_session.rollback()


def test_invalid_status_is_rejected(db_session: Session) -> None:
    with pytest.raises(IntegrityError):
        create_uploaded_file(db_session, status="invalid-status")
    db_session.rollback()


def test_unknown_user_is_rejected(db_session: Session) -> None:
    repository = UploadedFileRepository(db_session)
    with pytest.raises(IntegrityError):
        repository.create(
            uploaded_by=uuid.uuid4(),
            equipment_id="MOTOR-001",
            original_filename="unknown-user.csv",
            stored_filename=f"{uuid.uuid4()}.csv",
            file_path="data/uploads/unknown-user.csv",
            file_size=128,
            checksum=hashlib.sha256(b"unknown-user").hexdigest(),
        )
    db_session.rollback()


def test_delete_removes_uploaded_file(db_session: Session) -> None:
    repository = UploadedFileRepository(db_session)
    created = create_uploaded_file(db_session)
    uploaded_file_id = created.id
    repository.delete(created)
    assert repository.get_by_id(uploaded_file_id) is None
