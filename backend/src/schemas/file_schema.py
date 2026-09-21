from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UploadedFileResponse(BaseModel):
    """CSVアップロード情報のレスポンス。"""

    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID
    uploaded_by: UUID
    equipment_id: str
    original_filename: str
    stored_filename: str
    file_path: str
    file_size: int
    mime_type: str | None
    encoding: str
    checksum: str
    measurement_date: date | None
    status: str
    error_code: str | None
    error_message: str | None
    uploaded_at: datetime
    updated_at: datetime


class FileUploadResponse(BaseModel):
    """CSVアップロードAPIのレスポンス。"""

    message: str
    is_duplicate: bool
    uploaded_file: UploadedFileResponse