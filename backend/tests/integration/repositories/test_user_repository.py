import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.src.repositories.user_repository import (
    UserRepository,
)


def unique_login_id(prefix: str) -> str:
    """テストごとに重複しないlogin_idを生成する。"""

    return f"{prefix}-{uuid.uuid4().hex}"


def test_create_and_get_user_by_id(
    db_session: Session,
) -> None:
    """ユーザーを登録し、IDで取得できる。"""

    repository = UserRepository(db_session)
    login_id = unique_login_id("user-by-id")

    created_user = repository.create(
        login_id=login_id,
        password_hash="hashed-password",
        display_name="テストユーザー",
    )

    found_user = repository.get_by_id(
        created_user.id
    )

    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.login_id == login_id
    assert found_user.password_hash == "hashed-password"
    assert found_user.display_name == "テストユーザー"
    assert found_user.role == "user"
    assert found_user.is_active is True


def test_create_and_get_user_by_login_id(
    db_session: Session,
) -> None:
    """登録したユーザーをlogin_idで取得できる。"""

    repository = UserRepository(db_session)
    login_id = unique_login_id("user-by-login")

    created_user = repository.create(
        login_id=login_id,
        password_hash="hashed-password",
        display_name="Login ID検索ユーザー",
        role="admin",
        is_active=False,
    )

    found_user = repository.get_by_login_id(
        login_id
    )

    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.login_id == login_id
    assert found_user.role == "admin"
    assert found_user.is_active is False


def test_get_returns_none_for_unknown_user(
    db_session: Session,
) -> None:
    """存在しないユーザーではNoneを返す。"""

    repository = UserRepository(db_session)

    assert repository.get_by_id(uuid.uuid4()) is None

    unknown_login_id = unique_login_id(
        "unknown-user"
    )

    assert (
        repository.get_by_login_id(
            unknown_login_id
        )
        is None
    )


def test_exists_by_login_id(
    db_session: Session,
) -> None:
    """login_idの存在有無を確認できる。"""

    repository = UserRepository(db_session)
    login_id = unique_login_id("exists-user")

    assert repository.exists_by_login_id(
        login_id
    ) is False

    repository.create(
        login_id=login_id,
        password_hash="hashed-password",
        display_name="存在確認ユーザー",
    )

    assert repository.exists_by_login_id(
        login_id
    ) is True


def test_login_id_must_be_unique(
    db_session: Session,
) -> None:
    """同じlogin_idを重複登録できない。"""

    repository = UserRepository(db_session)
    login_id = unique_login_id("duplicate-user")

    repository.create(
        login_id=login_id,
        password_hash="hashed-password-1",
        display_name="重複確認ユーザー1",
    )

    with pytest.raises(IntegrityError):
        repository.create(
            login_id=login_id,
            password_hash="hashed-password-2",
            display_name="重複確認ユーザー2",
        )

    db_session.rollback()


def test_role_check_constraint_rejects_invalid_role(
    db_session: Session,
) -> None:
    """許可されていないRoleを登録できない。"""

    repository = UserRepository(db_session)

    with pytest.raises(IntegrityError):
        repository.create(
            login_id=unique_login_id(
                "invalid-role"
            ),
            password_hash="hashed-password",
            display_name="不正Roleユーザー",
            role="invalid-role",
        )

    db_session.rollback()


def test_delete_removes_user(
    db_session: Session,
) -> None:
    """登録したユーザーを削除できる。"""

    repository = UserRepository(db_session)
    login_id = unique_login_id("delete-user")

    created_user = repository.create(
        login_id=login_id,
        password_hash="hashed-password",
        display_name="削除対象ユーザー",
    )
    user_id = created_user.id

    repository.delete(created_user)

    assert repository.get_by_id(user_id) is None
    assert repository.exists_by_login_id(
        login_id
    ) is False
