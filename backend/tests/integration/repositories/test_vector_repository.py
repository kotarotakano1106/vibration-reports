import hashlib
import uuid
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.src.repositories.report_repository import ReportRepository
from backend.src.repositories.uploaded_file_repository import UploadedFileRepository
from backend.src.repositories.user_repository import UserRepository
from backend.src.repositories.vector_repository import VectorRepository

EMBEDDING_DIMENSIONS = 1536


def make_embedding(index: int = 0) -> list[float]:
    """指定位置だけ1.0の固定次元ベクトルを返す。"""
    embedding = [0.0] * EMBEDDING_DIMENSIONS
    embedding[index] = 1.0
    return embedding


def create_report(db_session: Session, equipment_id: str = "MOTOR-001"):
    """チャンクの外部キーに必要なレポートを作成する。"""
    suffix = uuid.uuid4().hex
    user = UserRepository(db_session).create(
        login_id=f"vector-user-{suffix}",
        password_hash="hashed-password",
        display_name="Vectorテストユーザー",
    )
    stored_filename = f"{uuid.uuid4()}.csv"
    uploaded_file = UploadedFileRepository(db_session).create(
        uploaded_by=user.id,
        equipment_id=equipment_id,
        original_filename="measurement.csv",
        stored_filename=stored_filename,
        file_path=f"data/uploads/{stored_filename}",
        file_size=128,
        checksum=hashlib.sha256(uuid.uuid4().bytes).hexdigest(),
        measurement_date=date(2026, 9, 1),
        mime_type="text/csv",
        status="completed",
    )
    report = ReportRepository(db_session).create(
        uploaded_file_id=uploaded_file.id,
        created_by=user.id,
        equipment_id=equipment_id,
        title="Vector検索テストレポート",
        record_count=3,
        minimum_value=1.0,
        maximum_value=3.0,
        average_value=2.0,
        anomaly_count=1,
        anomaly_details=[],
        status="requires_attention",
        ai_summary="テスト概要",
        ai_analysis="テスト分析",
        report_text="テスト本文",
        measurement_date=date(2026, 9, 1),
    )
    return report


def create_chunk(
    db_session: Session,
    report_id,
    *,
    chunk_index: int = 0,
    chunk_type: str = "analysis_summary",
    equipment_id: str = "MOTOR-001",
    measurement_date: date = date(2026, 9, 1),
    embedding: list[float] | None = None,
):
    """テスト用チャンクを作成する。"""
    return VectorRepository(db_session).create(
        report_id=report_id,
        chunk_index=chunk_index,
        chunk_type=chunk_type,
        content=f"チャンク{chunk_index}",
        embedding=embedding or make_embedding(chunk_index % 3),
        embedding_model="test-embedding-model",
        embedding_version="v1",
        equipment_id=equipment_id,
        measurement_date=measurement_date,
        metadata_json={"source": "integration-test"},
    )


def test_create_and_get_by_id(db_session: Session) -> None:
    repository = VectorRepository(db_session)
    report = create_report(db_session)
    created = create_chunk(db_session, report.id)

    found = repository.get_by_id(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.report_id == report.id
    assert found.chunk_type == "analysis_summary"
    assert found.metadata_json == {"source": "integration-test"}
    assert len(found.embedding) == EMBEDDING_DIMENSIONS


def test_get_by_report_and_index(db_session: Session) -> None:
    repository = VectorRepository(db_session)
    report = create_report(db_session)
    created = create_chunk(db_session, report.id, chunk_index=2)

    found = repository.get_by_report_and_index(report.id, 2)

    assert found is not None
    assert found.id == created.id


def test_get_returns_none_for_unknown_values(db_session: Session) -> None:
    repository = VectorRepository(db_session)

    assert repository.get_by_id(uuid.uuid4()) is None
    assert repository.get_by_report_and_index(uuid.uuid4(), 0) is None


def test_list_by_report_id_orders_by_chunk_index(db_session: Session) -> None:
    repository = VectorRepository(db_session)
    report = create_report(db_session)
    create_chunk(db_session, report.id, chunk_index=2)
    create_chunk(db_session, report.id, chunk_index=0)
    create_chunk(db_session, report.id, chunk_index=1)

    result = repository.list_by_report_id(report.id)

    assert [item.chunk_index for item in result] == [0, 1, 2]


def test_report_and_chunk_index_must_be_unique(db_session: Session) -> None:
    report = create_report(db_session)
    create_chunk(db_session, report.id, chunk_index=0)

    with pytest.raises(IntegrityError):
        create_chunk(db_session, report.id, chunk_index=0)

    db_session.rollback()


def test_chunk_index_must_be_non_negative(db_session: Session) -> None:
    report = create_report(db_session)

    with pytest.raises(IntegrityError):
        create_chunk(db_session, report.id, chunk_index=-1)

    db_session.rollback()


def test_unknown_report_is_rejected(db_session: Session) -> None:
    with pytest.raises(IntegrityError):
        create_chunk(db_session, uuid.uuid4())

    db_session.rollback()


def test_search_similar_orders_by_cosine_distance(db_session: Session) -> None:
    repository = VectorRepository(db_session)
    report = create_report(db_session)
    closest = create_chunk(
        db_session,
        report.id,
        chunk_index=0,
        embedding=make_embedding(0),
    )
    create_chunk(
        db_session,
        report.id,
        chunk_index=1,
        embedding=make_embedding(1),
    )

    result = repository.search_similar(
        query_embedding=make_embedding(0),
        limit=2,
    )

    assert len(result) == 2
    assert result[0]["report_chunk"].id == closest.id
    assert result[0]["distance"] == pytest.approx(0.0)
    assert result[0]["distance"] <= result[1]["distance"]


def test_search_similar_applies_filters_and_limit(db_session: Session) -> None:
    repository = VectorRepository(db_session)
    report_one = create_report(db_session, equipment_id="MOTOR-FILTER-001")
    report_two = create_report(db_session, equipment_id="MOTOR-FILTER-002")
    expected = create_chunk(
        db_session,
        report_one.id,
        chunk_index=0,
        chunk_type="recommendation",
        equipment_id="MOTOR-FILTER-001",
        measurement_date=date(2026, 9, 10),
        embedding=make_embedding(0),
    )
    create_chunk(
        db_session,
        report_one.id,
        chunk_index=1,
        chunk_type="analysis_summary",
        equipment_id="MOTOR-FILTER-001",
        measurement_date=date(2026, 9, 10),
        embedding=make_embedding(0),
    )
    create_chunk(
        db_session,
        report_two.id,
        chunk_index=0,
        chunk_type="recommendation",
        equipment_id="MOTOR-FILTER-002",
        measurement_date=date(2026, 9, 10),
        embedding=make_embedding(0),
    )

    result = repository.search_similar(
        query_embedding=make_embedding(0),
        limit=1,
        equipment_id="MOTOR-FILTER-001",
        measurement_date_from=date(2026, 9, 1),
        measurement_date_to=date(2026, 9, 30),
        chunk_types=["recommendation"],
    )

    assert len(result) == 1
    assert result[0]["report_chunk"].id == expected.id


def test_delete_by_report_id(db_session: Session) -> None:
    repository = VectorRepository(db_session)
    report = create_report(db_session)
    create_chunk(db_session, report.id, chunk_index=0)
    create_chunk(db_session, report.id, chunk_index=1)

    deleted_count = repository.delete_by_report_id(report.id)

    assert deleted_count == 2
    assert repository.list_by_report_id(report.id) == []


def test_deleting_report_cascades_to_chunks(
    db_session: Session,
) -> None:
    """Report削除時に関連Chunkも削除される。"""

    vector_repository = VectorRepository(db_session)
    report_repository = ReportRepository(db_session)

    report = create_report(db_session)
    chunk = create_chunk(
        db_session,
        report.id,
    )
    chunk_id = chunk.id

    report_repository.delete(report)

    db_session.expunge(chunk)

    assert (
        vector_repository.get_by_id(chunk_id)
        is None
    )

