import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.src.models.user import User


class UserRepository:
    """usersテーブルへのDB操作を担当するRepository。"""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        login_id: str,
        password_hash: str,
        display_name: str,
        role: str = "user",
        is_active: bool = True,
    ) -> User:
        """新しいユーザーをSessionへ追加する。"""

        user = User(
            login_id=login_id,
            password_hash=password_hash,
            display_name=display_name,
            role=role,
            is_active=is_active,
        )

        self._session.add(user)
        self._session.flush()
        self._session.refresh(user)

        return user

    def get_by_id(
        self,
        user_id: uuid.UUID,
    ) -> User | None:
        """UUIDを指定してユーザーを取得する。"""

        return self._session.get(
            User,
            user_id,
        )

    def get_by_login_id(
        self,
        login_id: str,
    ) -> User | None:
        """login_idを指定してユーザーを取得する。"""

        statement = select(User).where(
            User.login_id == login_id
        )

        return self._session.scalar(statement)

    def exists_by_login_id(
        self,
        login_id: str,
    ) -> bool:
        """login_idが存在するか確認する。"""

        statement = select(User.id).where(
            User.login_id == login_id
        )

        return self._session.scalar(statement) is not None

    def delete(
        self,
        user: User,
    ) -> None:
        """ユーザーをSessionから削除する。"""

        self._session.delete(user)
        self._session.flush()