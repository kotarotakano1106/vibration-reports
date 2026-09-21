from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import backend.src.services.file_service as file_service_module
from backend.src.repositories.user_repository import UserRepository

DEVELOPMENT_LOGIN_ID = "dev-user"
VALID_CSV = (
    b"measured_at,vibration_value\n"
    b"2026-09-01T10:00:00+09:00,1.5\n"
)


@pytest.fixture
def api_upload_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """APIアップロード先を一時ディレクトリへ差し替える。"""
    upload_directory = tmp_path / "data" / "uploads"
    monkeypatch.setattr(file_service_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        file_service_module,
        "DEFAULT_UPLOAD_DIRECTORY",
        upload_directory,
    )
    return upload_directory


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


def post_csv(
    api_client: TestClient,
    *,
    filename: str = "measurement.csv",
    content: bytes = VALID_CSV,
    content_type: str = "text/csv",
    equipment_id: str = "MOTOR-001",
):
    """CSVアップロードAPIを呼び出す。"""
    return api_client.post(
        "/api/v1/files",
        files={"file": (filename, content, content_type)},
        data={
            "equipment_id": equipment_id,
            "measurement_date": "2026-09-01",
            "encoding": "UTF-8",
        },
    )


def test_upload_csv_returns_500_without_development_user(
    api_client: TestClient,
    api_upload_directory: Path,
) -> None:
    """開発用ユーザーがない場合は500を返す。"""
    response = post_csv(api_client)

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "開発用ユーザーが登録されていません。"
    )
    assert not api_upload_directory.exists()


def test_upload_csv_saves_file_and_returns_response(
    api_client: TestClient,
    db_session: Session,
    api_upload_directory: Path,
) -> None:
    """正常なCSVを保存し、201レスポンスを返す。"""
    user = create_development_user(db_session)

    response = post_csv(api_client)

    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "CSVファイルをアップロードしました。"
    assert body["is_duplicate"] is False

    uploaded_file = body["uploaded_file"]
    assert uploaded_file["uploaded_by"] == str(user.id)
    assert uploaded_file["equipment_id"] == "MOTOR-001"
    assert uploaded_file["original_filename"] == "measurement.csv"
    assert uploaded_file["file_size"] == len(VALID_CSV)
    assert uploaded_file["mime_type"] == "text/csv"
    assert uploaded_file["encoding"] == "UTF-8"
    assert uploaded_file["measurement_date"] == "2026-09-01"
    assert uploaded_file["status"] == "uploaded"

    saved_files = list(api_upload_directory.glob("*.csv"))
    assert len(saved_files) == 1
    assert saved_files[0].read_bytes() == VALID_CSV


def test_upload_csv_returns_existing_record_for_duplicate(
    api_client: TestClient,
    db_session: Session,
    api_upload_directory: Path,
) -> None:
    """同一内容を再送した場合は既存情報を返す。"""
    create_development_user(db_session)

    first = post_csv(api_client, filename="first.csv")
    second = post_csv(api_client, filename="second.csv")

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["is_duplicate"] is False
    assert second.json()["is_duplicate"] is True
    assert second.json()["message"] == (
        "同一内容のCSVが登録済みのため、既存情報を返しました。"
    )
    assert (
        second.json()["uploaded_file"]["id"]
        == first.json()["uploaded_file"]["id"]
    )
    assert len(list(api_upload_directory.glob("*.csv"))) == 1


def test_upload_csv_rejects_empty_file(
    api_client: TestClient,
    db_session: Session,
    api_upload_directory: Path,
) -> None:
    """空ファイルでは400を返す。"""
    create_development_user(db_session)

    response = post_csv(api_client, content=b"")

    assert response.status_code == 400
    assert "空" in response.json()["detail"]
    assert list(api_upload_directory.glob("*")) == []


def test_upload_csv_rejects_invalid_extension(
    api_client: TestClient,
    db_session: Session,
    api_upload_directory: Path,
) -> None:
    """CSV以外の拡張子では400を返す。"""
    create_development_user(db_session)

    response = post_csv(api_client, filename="measurement.txt")

    assert response.status_code == 400
    assert "CSVファイルのみ" in response.json()["detail"]
    assert list(api_upload_directory.glob("*")) == []


def test_upload_csv_rejects_invalid_mime_type(
    api_client: TestClient,
    db_session: Session,
    api_upload_directory: Path,
) -> None:
    """許可されていないMIMEタイプでは400を返す。"""
    create_development_user(db_session)

    response = post_csv(
        api_client,
        content_type="application/pdf",
    )

    assert response.status_code == 400
    assert "MIMEタイプ" in response.json()["detail"]
    assert list(api_upload_directory.glob("*")) == []


def test_upload_csv_requires_file_and_equipment_id(
    api_client: TestClient,
    db_session: Session,
) -> None:
    """必須Multipart項目がない場合は422を返す。"""
    create_development_user(db_session)

    response = api_client.post("/api/v1/files")

    assert response.status_code == 422
