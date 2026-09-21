import pytest

from backend.src.core.security import (
    hash_password,
    verify_password,
)


def test_hash_password_returns_hash_different_from_plain_text() -> None:
    """平文とは異なるパスワードHashを生成する。"""
    plain_password = "StrongPassword-123!"

    hashed_password = hash_password(plain_password)

    assert isinstance(hashed_password, str)
    assert hashed_password
    assert hashed_password != plain_password


def test_hash_password_uses_random_salt() -> None:
    """同じ平文でも異なるHashを生成する。"""
    plain_password = "StrongPassword-123!"

    first_hash = hash_password(plain_password)
    second_hash = hash_password(plain_password)

    assert first_hash != second_hash
    assert verify_password(plain_password, first_hash) is True
    assert verify_password(plain_password, second_hash) is True


def test_verify_password_accepts_correct_password() -> None:
    """正しい平文パスワードを検証できる。"""
    plain_password = "CorrectPassword-123!"
    hashed_password = hash_password(plain_password)

    assert verify_password(plain_password, hashed_password) is True


def test_verify_password_rejects_incorrect_password() -> None:
    """誤った平文パスワードを拒否する。"""
    hashed_password = hash_password("CorrectPassword-123!")

    assert verify_password("WrongPassword-456!", hashed_password) is False


@pytest.mark.parametrize("plain_password", ["", None])
def test_hash_password_rejects_empty_value(
    plain_password: str | None,
) -> None:
    """空のパスワードを拒否する。"""
    with pytest.raises(ValueError):
        hash_password(plain_password)  # type: ignore[arg-type]


def test_verify_password_rejects_invalid_hash() -> None:
    """不正なHash文字列では検証に失敗する。"""
    with pytest.raises(Exception):  # noqa: B017
        verify_password(
            "Password-123!",
            "not-a-valid-password-hash",
        )
