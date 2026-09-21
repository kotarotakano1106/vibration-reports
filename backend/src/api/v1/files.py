from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from backend.src.db.dependencies import (
    get_db_session,
)
from backend.src.repositories.user_repository import (
    UserRepository,
)
from backend.src.schemas.file_schema import (
    FileUploadResponse,
    UploadedFileResponse,
)
from backend.src.services.file_service import (
    FileAlreadyExistsError,
    FileDatabaseError,
    FileEmptyError,
    FileExtensionError,
    FileMimeTypeError,
    FileNameError,
    FileSaveError,
    FileService,
    FileServiceError,
    FileSizeError,
)

router = APIRouter(
    prefix="/files",
    tags=["files"],
)


DEVELOPMENT_LOGIN_ID = "dev-user"


@router.post(
    "",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_csv_file(
    file: UploadFile = File(...),
    equipment_id: str = Form(...),
    measurement_date: date | None = Form(
        default=None,
    ),
    encoding: str = Form(
        default="UTF-8",
    ),
    session: Session = Depends(
        get_db_session,
    ),
):
    """CSVファイルを保存し、管理情報を登録する。"""

    user_repository = UserRepository(
        session,
    )

    user = user_repository.get_by_login_id(
        DEVELOPMENT_LOGIN_ID,
    )

    if user is None:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "開発用ユーザーが"
                "登録されていません。"
            ),
        )

    original_filename = file.filename

    if not original_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ファイル名がありません。",
        )

    try:
        file_content = await file.read()

        file_service = FileService(
            session,
        )

        result = file_service.save_csv(
            file_content=file_content,
            original_filename=original_filename,
            uploaded_by=user.id,
            equipment_id=equipment_id,
            measurement_date=measurement_date,
            mime_type=(
                file.content_type or "text/csv"
            ),
            encoding=encoding,
        )

    except (
        FileNameError,
        FileExtensionError,
        FileMimeTypeError,
        FileEmptyError,
        FileSizeError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except FileAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except FileSaveError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=str(exc),
        ) from exc

    except FileDatabaseError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=str(exc),
        ) from exc

    except FileServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    finally:
        await file.close()

    uploaded_file_response = (
        UploadedFileResponse.model_validate(
            result.uploaded_file,
        )
    )

    if result.is_duplicate:
        message = (
            "同一内容のCSVが登録済みのため、"
            "既存情報を返しました。"
        )
    else:
        message = (
            "CSVファイルをアップロードしました。"
        )

    return FileUploadResponse(
        message=message,
        is_duplicate=result.is_duplicate,
        uploaded_file=uploaded_file_response,
    )