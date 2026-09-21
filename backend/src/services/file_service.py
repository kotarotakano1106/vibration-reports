import hashlib
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from sqlalchemy.exc import IntegrityError

from backend.src.repositories.uploaded_file_repository import (
    UploadedFileRepository,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_UPLOAD_DIRECTORY = PROJECT_ROOT / "data" / "uploads"

DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024


class FileServiceError(Exception):
    """FileService共通エラー。"""


class FileNameError(FileServiceError):
    """ファイル名が不正な場合のエラー。"""


class FileExtensionError(FileServiceError):
    """拡張子が不正な場合のエラー。"""


class FileMimeTypeError(FileServiceError):
    """MIMEタイプが不正な場合のエラー。"""


class FileEmptyError(FileServiceError):
    """ファイルが空の場合のエラー。"""


class FileSizeError(FileServiceError):
    """ファイルサイズが上限を超えた場合のエラー。"""


class FileAlreadyExistsError(FileServiceError):
    """同じ内容のファイルが登録済みの場合のエラー。"""


class FileSaveError(FileServiceError):
    """ファイル保存に失敗した場合のエラー。"""


class FileDatabaseError(FileServiceError):
    """ファイル管理情報のDB登録に失敗した場合のエラー。"""


@dataclass(frozen=True)
class FileSaveResult:
    """ファイル保存結果。"""

    uploaded_file: object
    absolute_path: Path
    is_duplicate: bool


class FileService:
    """CSVファイルの保存とDB登録を担当するService。"""

    ALLOWED_EXTENSIONS: ClassVar[set[str]] = {
        ".csv",
    }

    ALLOWED_MIME_TYPES: ClassVar[set[str]] = {
        "text/csv",
        "application/csv",
        "application/vnd.ms-excel",
        "text/plain",
    }

    def __init__(
        self,
        session,
        upload_directory=None,
        max_file_size=DEFAULT_MAX_FILE_SIZE,
    ):
        self._session = session

        self._repository = UploadedFileRepository(
            session
        )

        if upload_directory is None:
            self._upload_directory = (
                DEFAULT_UPLOAD_DIRECTORY
            )
        else:
            self._upload_directory = Path(
                upload_directory
            )

        self._max_file_size = int(
            max_file_size
        )

        if self._max_file_size <= 0:
            raise ValueError(
                "max_file_sizeは0より大きい値を"
                "指定してください。"
            )

    def save_csv(
        self,
        *,
        file_content,
        original_filename,
        uploaded_by,
        equipment_id,
        measurement_date=None,
        mime_type="text/csv",
        encoding="UTF-8",
        reject_duplicate=False,
    ):
        """CSVファイルを保存して管理情報を登録する。"""

        self._validate_file_content(
            file_content
        )

        normalized_filename = (
            self._validate_filename(
                original_filename
            )
        )

        self._validate_extension(
            normalized_filename
        )

        normalized_mime_type = (
            self._validate_mime_type(
                mime_type
            )
        )

        self._validate_equipment_id(
            equipment_id
        )

        file_size = len(file_content)

        self._validate_file_size(
            file_size
        )

        checksum = self._calculate_checksum(
            file_content
        )

        existing_file = (
            self._repository.get_by_checksum(
                checksum
            )
        )

        if existing_file is not None:
            if reject_duplicate:
                raise FileAlreadyExistsError(
                    "同じ内容のCSVファイルが"
                    "既に登録されています。"
                    f" uploaded_file_id={existing_file.id}"
                )

            existing_path = (
                PROJECT_ROOT
                / existing_file.file_path
            )

            return FileSaveResult(
                uploaded_file=existing_file,
                absolute_path=existing_path,
                is_duplicate=True,
            )

        stored_filename = (
            f"{uuid.uuid4()}.csv"
        )

        absolute_path = (
            self._upload_directory
            / stored_filename
        )

        relative_path = absolute_path.relative_to(
            PROJECT_ROOT
        )

        temporary_path = absolute_path.with_suffix(
            ".csv.tmp"
        )

        self._upload_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            temporary_path.write_bytes(
                file_content
            )

            os.replace(
                temporary_path,
                absolute_path,
            )

        except OSError as exc:
            self._delete_file_if_exists(
                temporary_path
            )

            self._delete_file_if_exists(
                absolute_path
            )

            raise FileSaveError(
                "CSVファイルを保存できませんでした。"
                f" path={absolute_path}"
            ) from exc

        try:
            uploaded_file = self._repository.create(
                uploaded_by=uploaded_by,
                equipment_id=equipment_id.strip(),
                original_filename=normalized_filename,
                stored_filename=stored_filename,
                file_path=relative_path.as_posix(),
                file_size=file_size,
                checksum=checksum,
                measurement_date=measurement_date,
                mime_type=normalized_mime_type,
                encoding=encoding.strip(),
                status="uploaded",
            )

            self._session.commit()
            self._session.refresh(
                uploaded_file
            )

        except IntegrityError as exc:
            self._session.rollback()

            self._delete_file_if_exists(
                absolute_path
            )

            raise FileDatabaseError(
                "CSV管理情報の登録に失敗しました。"
                "DB制約を確認してください。"
            ) from exc

        except Exception:
            self._session.rollback()

            self._delete_file_if_exists(
                absolute_path
            )

            raise

        return FileSaveResult(
            uploaded_file=uploaded_file,
            absolute_path=absolute_path,
            is_duplicate=False,
        )

    def _validate_file_content(
        self,
        file_content,
    ):
        """ファイル内容を検証する。"""

        if not isinstance(
            file_content,
            bytes,
        ):
            raise FileServiceError(
                "file_contentはbytesで"
                "指定してください。"
            )

        if not file_content:
            raise FileEmptyError(
                "アップロードファイルが空です。"
            )

    def _validate_filename(
        self,
        original_filename,
    ):
        """元ファイル名を検証する。"""

        if not isinstance(
            original_filename,
            str,
        ):
            raise FileNameError(
                "ファイル名は文字列で"
                "指定してください。"
            )

        filename = original_filename.strip()

        if not filename:
            raise FileNameError(
                "ファイル名が空です。"
            )

        if filename in {".", ".."}:
            raise FileNameError(
                "ファイル名に相対パス要素を"
                "指定できません。"
            )

        if "\x00" in filename:
            raise FileNameError(
                "ファイル名に不正な文字が"
                "含まれています。"
            )

        basename = Path(filename).name

        if basename != filename:
            raise FileNameError(
                "ファイル名にディレクトリを"
                "含めることはできません。"
            )

        return basename

    def _validate_extension(
        self,
        filename,
    ):
        """CSV拡張子を確認する。"""

        extension = Path(
            filename
        ).suffix.lower()

        if extension not in self.ALLOWED_EXTENSIONS:
            raise FileExtensionError(
                "CSVファイルのみ登録できます。"
                f" extension={extension or 'なし'}"
            )

    def _validate_mime_type(
        self,
        mime_type,
    ):
        """MIMEタイプを確認する。"""

        if not isinstance(
            mime_type,
            str,
        ):
            raise FileMimeTypeError(
                "MIMEタイプは文字列で"
                "指定してください。"
            )

        normalized_mime_type = (
            mime_type
            .split(";", 1)[0]
            .strip()
            .lower()
        )

        if (
            normalized_mime_type
            not in self.ALLOWED_MIME_TYPES
        ):
            raise FileMimeTypeError(
                "許可されていないMIMEタイプです。"
                f" mime_type={normalized_mime_type}"
            )

        return normalized_mime_type

    def _validate_equipment_id(
        self,
        equipment_id,
    ):
        """設備IDを確認する。"""

        if not isinstance(
            equipment_id,
            str,
        ):
            raise FileServiceError(
                "equipment_idは文字列で"
                "指定してください。"
            )

        if not equipment_id.strip():
            raise FileServiceError(
                "equipment_idを空にできません。"
            )

    def _validate_file_size(
        self,
        file_size,
    ):
        """ファイルサイズを確認する。"""

        if file_size <= 0:
            raise FileEmptyError(
                "アップロードファイルが空です。"
            )

        if file_size > self._max_file_size:
            raise FileSizeError(
                "ファイルサイズが上限を"
                "超えています。"
                f" file_size={file_size}"
                f" max_file_size={self._max_file_size}"
            )

    def _calculate_checksum(
        self,
        file_content,
    ):
        """SHA-256チェックサムを生成する。"""

        return hashlib.sha256(
            file_content
        ).hexdigest()

    def _delete_file_if_exists(
        self,
        path,
    ):
        """ファイルが存在する場合だけ削除する。"""

        try:
            path.unlink(
                missing_ok=True
            )

        except OSError:
            pass