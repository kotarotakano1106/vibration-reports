from getpass import getpass

from sqlalchemy.exc import IntegrityError

from backend.src.core.security import (
    hash_password,
    verify_password,
)
from backend.src.db.session import SessionLocal
from backend.src.repositories.user_repository import (
    UserRepository,
)


TEST_LOGIN_ID = "dev-user"
TEST_DISPLAY_NAME = "開発用ユーザー"


def show_user(user) -> None:
    """秘密情報を除いてユーザー情報を表示する。"""

    print("ID:", user.id)
    print("login_id:", user.login_id)
    print("display_name:", user.display_name)
    print("role:", user.role)
    print("is_active:", user.is_active)
    print("created_at:", user.created_at)


def main() -> None:
    """開発用ユーザーの登録と取得を確認する。"""

    plain_password = getpass(
        "開発用ユーザーのパスワードを入力してください: "
    )

    if not plain_password:
        raise ValueError(
            "パスワードを空にすることはできません。"
        )

    with SessionLocal() as session:
        repository = UserRepository(session)

        existing_user = repository.get_by_login_id(
            TEST_LOGIN_ID
        )

        if existing_user is not None:
            print("登録済みユーザーを取得しました。")
            show_user(existing_user)

            password_matches = verify_password(
                plain_password,
                existing_user.password_hash,
            )

            print(
                "パスワード照合:",
                password_matches,
            )
            return

        hashed_password = hash_password(
            plain_password
        )

        try:
            created_user = repository.create(
                login_id=TEST_LOGIN_ID,
                password_hash=hashed_password,
                display_name=TEST_DISPLAY_NAME,
                role="user",
                is_active=True,
            )

            session.commit()
            session.refresh(created_user)

        except IntegrityError as exc:
            session.rollback()

            raise RuntimeError(
                "ユーザー登録に失敗しました。"
                "login_idの重複または制約違反を"
                "確認してください。"
            ) from exc

        retrieved_user = repository.get_by_login_id(
            TEST_LOGIN_ID
        )

        if retrieved_user is None:
            raise RuntimeError(
                "登録したユーザーを取得できませんでした。"
            )

        print("ユーザー登録: 成功")
        print("ユーザー取得: 成功")
        show_user(retrieved_user)

        print(
            "平文保存ではない:",
            retrieved_user.password_hash
            != plain_password,
        )

        print(
            "パスワード照合:",
            verify_password(
                plain_password,
                retrieved_user.password_hash,
            ),
        )


if __name__ == "__main__":
    try:
        main()

    except Exception as exc:
        print(
            "Repository確認失敗:",
            type(exc).__name__,
            str(exc),
        )
        raise SystemExit(1) from exc
