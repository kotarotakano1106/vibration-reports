import hashlib
from pathlib import Path
from unittest.mock import Mock

import pytest

from backend.src.services.file_service import (
    FileEmptyError,
    FileExtensionError,
    FileMimeTypeError,
    FileNameError,
    FileService,
    FileServiceError,
    FileSizeError,
)


@pytest.fixture
def file_service(
    tmp_path: Path,
) -> FileService:
    """テスト用FileServiceを作成する。"""

    return FileService(
        session=Mock(),
        upload_directory=tmp_path,
        max_file_size=100,
    )


def test_init_raises_when_max_file_size_is_zero(
    tmp_path: Path,
) -> None:
    """最大サイズが0の場合は初期化に失敗する。"""

    with pytest.raises(ValueError):
        FileService(
            session=Mock(),
            upload_directory=tmp_path,
            max_file_size=0,
        )


def test_init_raises_when_max_file_size_is_negative(
    tmp_path: Path,
) -> None:
    """最大サイズが負数の場合は初期化に失敗する。"""

    with pytest.raises(ValueError):
        FileService(
            session=Mock(),
            upload_directory=tmp_path,
            max_file_size=-1,
        )


@pytest.mark.parametrize(
    "filename",
    [
        "measurement.csv",
        "MEASUREMENT.CSV",
        "equipment-data.CsV",
    ],
)
def test_validate_extension_accepts_csv(
    file_service: FileService,
    filename: str,
) -> None:
    """CSV拡張子を大文字小文字に関係なく許可する。"""

    file_service._validate_extension(filename)


@pytest.mark.parametrize(
    "filename",
    [
        "measurement.txt",
        "measurement.xlsx",
        "measurement",
        "measurement.csv.exe",
    ],
)
def test_validate_extension_rejects_non_csv(
    file_service: FileService,
    filename: str,
) -> None:
    """CSV以外の拡張子を拒否する。"""

    with pytest.raises(FileExtensionError):
        file_service._validate_extension(filename)


@pytest.mark.parametrize(
    ("mime_type", "expected"),
    [
        ("text/csv", "text/csv"),
        ("TEXT/CSV", "text/csv"),
        (
            "text/csv; charset=UTF-8",
            "text/csv",
        ),
        (
            " application/vnd.ms-excel ",
            "application/vnd.ms-excel",
        ),
        ("text/plain", "text/plain"),
    ],
)
def test_validate_mime_type_accepts_allowed_type(
    file_service: FileService,
    mime_type: str,
    expected: str,
) -> None:
    """許可されたMIMEタイプを正規化して返す。"""

    result = file_service._validate_mime_type(
        mime_type
    )

    assert result == expected


@pytest.mark.parametrize(
    "mime_type",
    [
        "application/pdf",
        "application/octet-stream",
        "",
    ],
)
def test_validate_mime_type_rejects_disallowed_type(
    file_service: FileService,
    mime_type: str,
) -> None:
    """許可されていないMIMEタイプを拒否する。"""

    with pytest.raises(FileMimeTypeError):
        file_service._validate_mime_type(
            mime_type
        )


def test_validate_mime_type_rejects_non_string(
    file_service: FileService,
) -> None:
    """MIMEタイプが文字列でない場合は拒否する。"""

    with pytest.raises(FileMimeTypeError):
        file_service._validate_mime_type(
            None
        )


@pytest.mark.parametrize(
    "equipment_id",
    [
        "MOTOR-001",
        " MOTOR-001 ",
        "設備-001",
    ],
)
def test_validate_equipment_id_accepts_non_empty_string(
    file_service: FileService,
    equipment_id: str,
) -> None:
    """空でない設備IDを許可する。"""

    file_service._validate_equipment_id(
        equipment_id
    )


@pytest.mark.parametrize(
    "equipment_id",
    [
        "",
        " ",
        "\t",
    ],
)
def test_validate_equipment_id_rejects_empty_string(
    file_service: FileService,
    equipment_id: str,
) -> None:
    """空の設備IDを拒否する。"""

    with pytest.raises(FileServiceError):
        file_service._validate_equipment_id(
            equipment_id
        )


def test_validate_equipment_id_rejects_non_string(
    file_service: FileService,
) -> None:
    """設備IDが文字列でない場合は拒否する。"""

    with pytest.raises(FileServiceError):
        file_service._validate_equipment_id(
            123
        )


@pytest.mark.parametrize(
    "file_size",
    [
        1,
        50,
        100,
    ],
)
def test_validate_file_size_accepts_limit_or_less(
    file_service: FileService,
    file_size: int,
) -> None:
    """上限以下のファイルサイズを許可する。"""

    file_service._validate_file_size(
        file_size
    )


@pytest.mark.parametrize(
    "file_size",
    [
        0,
        -1,
    ],
)
def test_validate_file_size_rejects_empty_file(
    file_service: FileService,
    file_size: int,
) -> None:
    """0以下のファイルサイズを空ファイルとして拒否する。"""

    with pytest.raises(FileEmptyError):
        file_service._validate_file_size(
            file_size
        )


def test_validate_file_size_rejects_over_limit(
    file_service: FileService,
) -> None:
    """上限を超えるファイルサイズを拒否する。"""

    with pytest.raises(FileSizeError):
        file_service._validate_file_size(
            101
        )


def test_calculate_checksum_returns_sha256(
    file_service: FileService,
) -> None:
    """ファイル内容からSHA-256を生成する。"""

    file_content = b"sample vibration data"

    result = file_service._calculate_checksum(
        file_content
    )

    assert result == hashlib.sha256(
        file_content
    ).hexdigest()
    assert len(result) == 64


def test_delete_file_if_exists_removes_file(
    file_service: FileService,
    tmp_path: Path,
) -> None:
    """存在するファイルを削除する。"""

    target = tmp_path / "delete-target.csv"
    target.write_bytes(b"data")

    file_service._delete_file_if_exists(
        target
    )

    assert not target.exists()


def test_delete_file_if_exists_ignores_missing_file(
    file_service: FileService,
    tmp_path: Path,
) -> None:
    """存在しないファイルの削除でも例外を送出しない。"""

    target = tmp_path / "not-found.csv"

    file_service._delete_file_if_exists(
        target
    )

    assert not target.exists()


@pytest.mark.parametrize(
    "filename",
    [
        "",
        " ",
        ".",
        "..",
    ],
)
def test_validate_filename_rejects_invalid_name(
    file_service: FileService,
    filename: str,
) -> None:
    """不正なファイル名を拒否する。"""

    with pytest.raises(FileNameError):
        file_service._validate_filename(
            filename
        )
