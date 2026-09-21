from backend.src.db.session import SessionLocal


def get_db_session():
    """FastAPIリクエスト用のDB Sessionを提供する。"""

    session = SessionLocal()

    try:
        yield session

    finally:
        session.close()