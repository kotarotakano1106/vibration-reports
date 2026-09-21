from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.src.core.config import get_settings
from backend.src.db.dependencies import get_db_session
from backend.src.main import app

TEST_DATABASE_SUFFIX = "_test"


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine]:
    """Integration Test専用のDB Engineを作成する。"""
    get_settings.cache_clear()
    settings = get_settings()
    database_url = settings.create_database_url()
    database_name = database_url.database or ""

    if not database_name.endswith(TEST_DATABASE_SUFFIX):
        pytest.exit(
            "Integration Testを中止しました。"
            "接続先DB名が_testで終わっていません。"
            f" database={database_name}",
            returncode=2,
        )

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )

    with engine.connect() as connection:
        connected_database = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

    if connected_database != database_name:
        engine.dispose()
        pytest.exit(
            "Integration Testを中止しました。"
            "設定DBと実接続DBが一致しません。",
            returncode=2,
        )

    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_engine: Engine) -> Generator[Session]:
    """テストごとにRollbackされるDB Sessionを作成する。"""
    connection = test_engine.connect()
    transaction = connection.begin()
    testing_session_local = sessionmaker(
        bind=connection,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    session = testing_session_local()

    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture
def api_client(db_session: Session) -> Generator[TestClient]:
    """DB依存関係をテストSessionへ差し替えたAPI Clientを返す。"""

    def override_get_db_session() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
