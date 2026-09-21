from sqlalchemy import text
from sqlalchemy.orm import Session


def test_connects_to_integration_test_database(
    db_session: Session,
) -> None:
    """Integration Test専用DBへ接続している。"""

    database_name = db_session.execute(
        text("SELECT current_database()")
    ).scalar_one()

    assert database_name == "vibration_reports_test"


def test_required_tables_exist(
    db_session: Session,
) -> None:
    """Migrationで必要なテーブルが作成されている。"""

    table_names = set(
        db_session.execute(
            text(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                """
            )
        ).scalars()
    )

    assert {
        "alembic_version",
        "users",
        "uploaded_files",
        "reports",
        "report_chunks",
    }.issubset(table_names)


def test_vector_extension_is_enabled(
    db_session: Session,
) -> None:
    """テストDBでpgvectorが有効になっている。"""

    extension_name = db_session.execute(
        text(
            """
            SELECT extname
            FROM pg_extension
            WHERE extname = 'vector'
            """
        )
    ).scalar_one()

    assert extension_name == "vector"
