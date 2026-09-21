import hashlib
import uuid
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import backend.src.api.v1.measurements as measurements_module
from backend.src.repositories.uploaded_file_repository import UploadedFileRepository
from backend.src.repositories.user_repository import UserRepository

VALID_CSV = (
    "measured_at,vibration_value\n"
    "2026-09-01T10:00:02+09:00,3.0\n"
    "2026-09-01T10:00:00+09:00,1.0\n"
    "2026-09-01T10:00:01+09:00,2.0\n"
)


@pytest.fixture
def measurement_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """測定値APIが参照するProject Rootを一時領域へ差し替える。"""
    monkeypatch.setattr(
        measurements_module,
        "PROJECT_ROOT",
        tmp_path,
    )
    return tmp_path


def create_uploaded_file(
    db_session: Session,
    measurement_root: Path,
    *,
    csv_content: str = VALID_CSV,
    create_physical_file: bool = True,
    path_is_directory: bool = False,
):
    """API確認用のCSV管理情報と物理ファイルを作成する。"""
    suffix = uuid.uuid4().hex
    user = UserRepository(db_session).create(
        login_id=f"measurements-api-{suffix}",
        password_hash="hashed-password",
        display_name="測定値APIテストユーザー",
    )

    stored_filename = f"{uuid.uuid4()}.csv"
    relative_path = Path("data") / "uploads" / stored_filename
    absolute_path = measurement_root / relative_path

    if create_physical_file:
        if path_is_directory:
            absolute_path.mkdir(parents=True, exist_ok=True)
        else:
            absolute_path.parent.mkdir(parents=True, exist_ok=True)
            absolute_path.write_text(csv_content, encoding="utf-8")

    uploaded_file = UploadedFileRepository(db_session).create(
        uploaded_by=user.id,
        equipment_id="MOTOR-MEASURE-001",
        original_filename="measurement.csv",
        stored_filename=stored_filename,
        file_path=relative_path.as_posix(),
        file_size=max(1, len(csv_content.encode("utf-8"))),
        checksum=hashlib.sha256(csv_content.encode("utf-8")).hexdigest(),
        measurement_date=date(2026, 9, 1),
        mime_type="text/csv",
        encoding="UTF-8",
        status="uploaded",
    )

    return uploaded_file, absolute_path


def test_get_measurements_returns_sorted_points_and_anomaly_flags(
    api_client: TestClient,
    db_session: Session,
    measurement_root: Path,
) -> None:
    """CSVを日時順に返し、閾値超過を異常として判定する。"""
    uploaded_file, _ = create_uploaded_file(db_session, measurement_root)

    response = api_client.get(
        f"/api/v1/files/{uploaded_file.id}/measurements",
        params={"threshold_value": 2.0},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["uploaded_file_id"] == str(uploaded_file.id)
    assert body["equipment_id"] == "MOTOR-MEASURE-001"
    assert body["measurement_date"] == "2026-09-01"
    assert body["measurement_count"] == 3
    assert body["threshold_value"] == 2.0

    points = body["measurements"]
    assert [point["vibration_value"] for point in points] == [1.0, 2.0, 3.0]
    assert [point["is_anomaly"] for point in points] == [False, False, True]
    assert [point["measured_at"] for point in points] == sorted(
        point["measured_at"] for point in points
    )


def test_get_measurements_uses_default_threshold(
    api_client: TestClient,
    db_session: Session,
    measurement_root: Path,
) -> None:
    """Queryを省略した場合は既定閾値2.0を使用する。"""
    uploaded_file, _ = create_uploaded_file(db_session, measurement_root)

    response = api_client.get(
        f"/api/v1/files/{uploaded_file.id}/measurements"
    )

    assert response.status_code == 200
    assert response.json()["threshold_value"] == 2.0


def test_get_measurements_returns_404_for_unknown_record(
    api_client: TestClient,
    measurement_root: Path,
) -> None:
    """存在しないCSV管理情報では404を返す。"""
    response = api_client.get(
        f"/api/v1/files/{uuid.uuid4()}/measurements"
    )

    assert response.status_code == 404
    assert "CSV管理情報" in response.json()["detail"]


def test_get_measurements_returns_404_when_physical_file_is_missing(
    api_client: TestClient,
    db_session: Session,
    measurement_root: Path,
) -> None:
    """物理CSVが存在しない場合は404を返す。"""
    uploaded_file, _ = create_uploaded_file(
        db_session,
        measurement_root,
        create_physical_file=False,
    )

    response = api_client.get(
        f"/api/v1/files/{uploaded_file.id}/measurements"
    )

    assert response.status_code == 404
    assert "CSV実ファイル" in response.json()["detail"]


def test_get_measurements_returns_404_when_path_is_directory(
    api_client: TestClient,
    db_session: Session,
    measurement_root: Path,
) -> None:
    """保存先がディレクトリの場合は404を返す。"""
    uploaded_file, _ = create_uploaded_file(
        db_session,
        measurement_root,
        path_is_directory=True,
    )

    response = api_client.get(
        f"/api/v1/files/{uploaded_file.id}/measurements"
    )

    assert response.status_code == 404
    assert "ファイルではありません" in response.json()["detail"]


def test_get_measurements_returns_400_for_invalid_csv(
    api_client: TestClient,
    db_session: Session,
    measurement_root: Path,
) -> None:
    """不正なCSV内容では400を返す。"""
    uploaded_file, _ = create_uploaded_file(
        db_session,
        measurement_root,
        csv_content=(
            "measured_at,vibration_value\n"
            "invalid-date,invalid-value\n"
        ),
    )

    response = api_client.get(
        f"/api/v1/files/{uploaded_file.id}/measurements"
    )

    assert response.status_code == 400


@pytest.mark.parametrize("threshold_value", [0, -1])
def test_get_measurements_rejects_non_positive_threshold(
    api_client: TestClient,
    threshold_value: int,
    measurement_root: Path,
) -> None:
    """0以下の閾値では422を返す。"""
    response = api_client.get(
        f"/api/v1/files/{uuid.uuid4()}/measurements",
        params={"threshold_value": threshold_value},
    )

    assert response.status_code == 422


def test_get_measurements_rejects_invalid_uuid(
    api_client: TestClient,
    measurement_root: Path,
) -> None:
    """不正なUUIDでは422を返す。"""
    response = api_client.get(
        "/api/v1/files/not-a-uuid/measurements"
    )

    assert response.status_code == 422
