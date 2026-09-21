from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    """平文パスワードを安全なハッシュへ変換する。"""

    if not plain_password:
        raise ValueError(
            "パスワードを空にすることはできません。"
        )

    return password_hash.hash(plain_password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """平文パスワードと保存済みハッシュを照合する。"""

    return password_hash.verify(
        plain_password,
        hashed_password,
    )