import uuid
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.src.models.uploaded_file import UploadedFile


class UploadedFileRepository:
    """uploaded_filesテーブルへのDB操作を担当するRepository。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        uploaded_by: uuid.UUID,
        equipment_id: str,
        original_filename: str,
        stored_filename: str,
        file_path: str,
        file_size: int,
        checksum: str,
        measurement_date: date | None = None,
        mime_type: str | None = None,
        encoding: str = "UTF-8",
        status: str = "uploaded",
    ) -> UploadedFile:
        """CSVファイルの管理情報をSessionへ追加する。"""

        uploaded_file = UploadedFile(
            uploaded_by=uploaded_by,
            equipment_id=equipment_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            encoding=encoding,
            checksum=checksum,
            measurement_date=measurement_date,
            status=status,
        )

        self._session.add(uploaded_file)
        self._session.flush()
        self._session.refresh(uploaded_file)

        return uploaded_file

    def get_by_id(
        self,
        uploaded_file_id: uuid.UUID,
    ) -> UploadedFile | None:
        """UUIDでCSV管理情報を取得する。"""

        return self._session.get(
            UploadedFile,
            uploaded_file_id,
        )

    def get_by_stored_filename(
        self,
        stored_filename: str,
    ) -> UploadedFile | None:
        """保存ファイル名でCSV管理情報を取得する。"""

        statement = select(UploadedFile).where(
            UploadedFile.stored_filename == stored_filename
        )

        return self._session.scalar(statement)

    def get_by_checksum(
        self,
        checksum: str,
    ) -> UploadedFile | None:
        """チェックサムでCSV管理情報を取得する。"""

        statement = select(UploadedFile).where(
            UploadedFile.checksum == checksum
        )

        return self._session.scalar(statement)

    def list_by_equipment_id(
        self,
        equipment_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ):
        """設備IDに紐づくCSV管理情報を取得する。"""

        statement = (
            select(UploadedFile)
            .where(
                UploadedFile.equipment_id == equipment_id
            )
            .order_by(
                UploadedFile.uploaded_at.desc()
            )
            .offset(offset)
            .limit(limit)
        )

        return list(
            self._session.scalars(statement).all()
        )

    def update_status(
        self,
        uploaded_file: UploadedFile,
        *,
        status: str,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> UploadedFile:
        """CSV処理状態とエラー情報を更新する。"""

        uploaded_file.status = status
        uploaded_file.error_code = error_code
        uploaded_file.error_message = error_message
        uploaded_file.updated_at = datetime.now().astimezone()

        self._session.flush()
        self._session.refresh(uploaded_file)

        return uploaded_file

    def delete(
        self,
        uploaded_file: UploadedFile,
    ) -> None:
        """CSV管理情報をSessionから削除する。"""

        self._session.delete(uploaded_file)
        self._session.flush()