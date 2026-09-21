import hashlib
import uuid
from datetime import date

from sqlalchemy.exc import IntegrityError

from backend.src.db.session import SessionLocal
from backend.src.repositories.uploaded_file_repository import (
    UploadedFileRepository,
)
from backend.src.repositories.user_repository import (
    UserRepository,
)


TEST_LOGIN_ID = "dev-user"
TEST_EQUIPMENT_ID = "MOTOR-001"
TEST_ORIGINAL_FILENAME = "vibration-MOTOR-001-20260901.csv"

TEST_FILE_CONTENT = (
    "measured_at,vibration_value\n"
    "2026-09-01T09:00:00+09:00,0.40\n"
    "2026-09-01T09:00:10+09:00,0.60\n"
    "2026-09-01T09:00:20+09:00,2.50\n"
)


def show_uploaded_file(uploaded_file):
    print("ID:", uploaded_file.id)
    print("uploaded_by:", uploaded_file.uploaded_by)
    print("equipment_id:", uploaded_file.equipment_id)
    print(
        "original_filename:",
        uploaded_file.original_filename,
    )
    print(
        "stored_filename:",
        uploaded_file.stored_filename,
    )
    print("file_path:", uploaded_file.file_path)
    print("file_size:", uploaded_file.file_size)
    print("mime_type:", uploaded_file.mime_type)
    print("encoding:", uploaded_file.encoding)
    print(
        "measurement_date:",
        uploaded_file.measurement_date,
    )
    print("status:", uploaded_file.status)
    print("uploaded_at:", uploaded_file.uploaded_at)


def main():
    file_bytes = TEST_FILE_CONTENT.encode("utf-8")

    checksum = hashlib.sha256(
        file_bytes
    ).hexdigest()

    with SessionLocal() as session:
        user_repository = UserRepository(session)

        file_repository = UploadedFileRepository(
            session
        )

        user = user_repository.get_by_login_id(
            TEST_LOGIN_ID
        )

        if user is None:
            raise RuntimeError(
                "dev-userが存在しません。"
                "UserRepositoryの確認を先に"
                "実行してください。"
            )

        existing_file = (
            file_repository.get_by_checksum(
                checksum
            )
        )

        if existing_file is not None:
            print(
                "登録済みCSV管理情報を取得しました。"
            )
            show_uploaded_file(existing_file)
            return

        stored_filename = f"{uuid.uuid4()}.csv"

        try:
            created_file = file_repository.create(
                uploaded_by=user.id,
                equipment_id=TEST_EQUIPMENT_ID,
                original_filename=(
                    TEST_ORIGINAL_FILENAME
                ),
                stored_filename=stored_filename,
                file_path=(
                    f"data/uploads/{stored_filename}"
                ),
                file_size=len(file_bytes),
                checksum=checksum,
                measurement_date=date(
                    2026,
                    9,
                    1,
                ),
                mime_type="text/csv",
                encoding="UTF-8",
                status="uploaded",
            )

            session.commit()
            session.refresh(created_file)

        except IntegrityError as exc:
            session.rollback()

            raise RuntimeError(
                "CSV管理情報の登録に失敗しました。"
                "DB制約を確認してください。"
            ) from exc

        retrieved_file = file_repository.get_by_id(
            created_file.id
        )

        if retrieved_file is None:
            raise RuntimeError(
                "登録したCSV管理情報を"
                "取得できませんでした。"
            )

        print("CSV管理情報登録: 成功")
        print("IDによる取得: 成功")

        show_uploaded_file(retrieved_file)

        file_repository.update_status(
            retrieved_file,
            status="processing",
        )

        session.commit()
        session.refresh(retrieved_file)

        print("status更新: 成功")
        print(
            "更新後status:",
            retrieved_file.status,
        )


if __name__ == "__main__":
    try:
        main()

    except Exception as exc:
        print(
            "UploadedFileRepository確認失敗:",
            type(exc).__name__,
            str(exc),
        )

        raise SystemExit(1) from exc