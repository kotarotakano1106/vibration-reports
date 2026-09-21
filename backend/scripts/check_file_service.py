from datetime import date

from backend.src.db.session import SessionLocal
from backend.src.repositories.user_repository import (
    UserRepository,
)
from backend.src.services.file_service import (
    FileEmptyError,
    FileExtensionError,
    FileService,
    FileServiceError,
)


TEST_LOGIN_ID = "dev-user"

TEST_CSV_CONTENT = (
    "measured_at,vibration_value\n"
    "2026-09-02T09:00:00+09:00,0.45\n"
    "2026-09-02T09:00:10+09:00,0.70\n"
    "2026-09-02T09:00:20+09:00,2.80\n"
    "2026-09-02T09:00:30+09:00,0.55\n"
)


def show_result(result):
    """ファイル保存結果を表示する。"""

    uploaded_file = result.uploaded_file

    print(
        "重複ファイル:",
        result.is_duplicate,
    )
    print(
        "uploaded_file_id:",
        uploaded_file.id,
    )
    print(
        "original_filename:",
        uploaded_file.original_filename,
    )
    print(
        "stored_filename:",
        uploaded_file.stored_filename,
    )
    print(
        "file_path:",
        uploaded_file.file_path,
    )
    print(
        "file_size:",
        uploaded_file.file_size,
    )
    print(
        "checksum:",
        uploaded_file.checksum,
    )
    print(
        "equipment_id:",
        uploaded_file.equipment_id,
    )
    print(
        "measurement_date:",
        uploaded_file.measurement_date,
    )
    print(
        "status:",
        uploaded_file.status,
    )
    print(
        "実ファイルパス:",
        result.absolute_path,
    )
    print(
        "実ファイル存在:",
        result.absolute_path.exists(),
    )


def check_valid_file(user):
    """正常なCSV保存を確認する。"""

    file_content = TEST_CSV_CONTENT.encode(
        "utf-8"
    )

    with SessionLocal() as session:
        service = FileService(session)

        result = service.save_csv(
            file_content=file_content,
            original_filename=(
                "vibration-MOTOR-001-20260902.csv"
            ),
            uploaded_by=user.id,
            equipment_id="MOTOR-001",
            measurement_date=date(
                2026,
                9,
                2,
            ),
            mime_type="text/csv",
            encoding="UTF-8",
        )

        print("=== 正常CSV保存 ===")
        show_result(result)

        if not result.is_duplicate:
            if not result.absolute_path.exists():
                raise RuntimeError(
                    "保存したCSVファイルが"
                    "存在しません。"
                )

            saved_content = (
                result.absolute_path.read_bytes()
            )

            if saved_content != file_content:
                raise RuntimeError(
                    "保存後のCSV内容が"
                    "元データと一致しません。"
                )

        print("正常CSV保存: 成功")

    return file_content


def check_duplicate_file(
    user,
    file_content,
):
    """重複ファイルの取得を確認する。"""

    with SessionLocal() as session:
        service = FileService(session)

        result = service.save_csv(
            file_content=file_content,
            original_filename=(
                "duplicate-name.csv"
            ),
            uploaded_by=user.id,
            equipment_id="MOTOR-001",
            measurement_date=date(
                2026,
                9,
                2,
            ),
            mime_type="text/csv",
        )

        print()
        print("=== 重複CSV確認 ===")
        print(
            "重複ファイル:",
            result.is_duplicate,
        )
        print(
            "既存uploaded_file_id:",
            result.uploaded_file.id,
        )

        if not result.is_duplicate:
            raise RuntimeError(
                "重複ファイルとして"
                "判定されませんでした。"
            )

        print("重複CSVの検出: 成功")


def check_invalid_extension(user):
    """CSV以外の拡張子を拒否できるか確認する。"""

    with SessionLocal() as session:
        service = FileService(session)

        try:
            service.save_csv(
                file_content=b"sample",
                original_filename="sample.txt",
                uploaded_by=user.id,
                equipment_id="MOTOR-001",
                mime_type="text/plain",
            )

        except FileExtensionError as exc:
            print()
            print("不正拡張子の検出: 成功")
            print("エラー内容:", str(exc))
            return

    raise RuntimeError(
        "CSV以外の拡張子を"
        "拒否できませんでした。"
    )


def check_empty_file(user):
    """空ファイルを拒否できるか確認する。"""

    with SessionLocal() as session:
        service = FileService(session)

        try:
            service.save_csv(
                file_content=b"",
                original_filename="empty.csv",
                uploaded_by=user.id,
                equipment_id="MOTOR-001",
                mime_type="text/csv",
            )

        except FileEmptyError as exc:
            print()
            print("空ファイルの検出: 成功")
            print("エラー内容:", str(exc))
            return

    raise RuntimeError(
        "空ファイルを拒否できませんでした。"
    )


def main():
    """FileServiceの基本動作を確認する。"""

    with SessionLocal() as session:
        user_repository = UserRepository(session)

        user = user_repository.get_by_login_id(
            TEST_LOGIN_ID
        )

        if user is None:
            raise RuntimeError(
                "dev-userが存在しません。"
            )

        session.expunge(user)

    print("=== FileService確認 ===")
    print("アップロードユーザー:", user.login_id)

    file_content = check_valid_file(user)

    check_duplicate_file(
        user,
        file_content,
    )

    check_invalid_extension(user)
    check_empty_file(user)

    print()
    print("FileServiceの全確認: 成功")


if __name__ == "__main__":
    try:
        main()

    except FileServiceError as exc:
        print(
            "FileService確認失敗:",
            type(exc).__name__,
            str(exc),
        )
        raise SystemExit(1) from exc

    except Exception as exc:
        print(
            "予期しないエラー:",
            type(exc).__name__,
            str(exc),
        )
        raise SystemExit(1) from exc