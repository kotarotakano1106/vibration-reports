import uuid
from datetime import date
from typing import Any, cast

from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from backend.src.models.report_chunk import ReportChunk


class VectorRepository:
    """report_chunksテーブルへのDB操作を担当するRepository。"""

    def __init__(self, session: Session):
        self._session = session

    def create(
        self,
        *,
        report_id: uuid.UUID,
        chunk_index: int,
        chunk_type: str,
        content: str,
        embedding,
        embedding_model: str,
        equipment_id: str,
        measurement_date: date | None = None,
        embedding_version: str | None = None,
        metadata_json: dict | None = None,
    ):
        """RAG検索用チャンクをSessionへ追加する。"""

        report_chunk = ReportChunk(
            report_id=report_id,
            chunk_index=chunk_index,
            chunk_type=chunk_type,
            content=content,
            embedding=embedding,
            embedding_model=embedding_model,
            embedding_version=embedding_version,
            equipment_id=equipment_id,
            measurement_date=measurement_date,
            metadata_json=metadata_json or {},
        )

        self._session.add(report_chunk)
        self._session.flush()
        self._session.refresh(report_chunk)

        return report_chunk

    def get_by_id(
        self,
        report_chunk_id: uuid.UUID,
    ):
        """UUIDでチャンクを取得する。"""

        return self._session.get(
            ReportChunk,
            report_chunk_id,
        )

    def get_by_report_and_index(
        self,
        report_id: uuid.UUID,
        chunk_index: int,
    ):
        """レポートIDとチャンク番号で取得する。"""

        statement = select(ReportChunk).where(
            ReportChunk.report_id == report_id,
            ReportChunk.chunk_index == chunk_index,
        )

        return self._session.scalar(statement)

    def list_by_report_id(
        self,
        report_id: uuid.UUID,
    ):
        """レポートに属するチャンク一覧を取得する。"""

        statement = (
            select(ReportChunk)
            .where(ReportChunk.report_id == report_id)
            .order_by(ReportChunk.chunk_index.asc())
        )

        return list(self._session.scalars(statement).all())

    def search_similar(
        self,
        *,
        query_embedding,
        limit: int = 5,
        equipment_id: str | None = None,
        measurement_date_from: date | None = None,
        measurement_date_to: date | None = None,
        chunk_types: list[str] | None = None,
    ):
        """コサイン距離で類似チャンクを検索する。"""

        distance = ReportChunk.embedding.cosine_distance(query_embedding).label("distance")

        statement = select(
            ReportChunk,
            distance,
        )

        if equipment_id is not None:
            statement = statement.where(ReportChunk.equipment_id == equipment_id)

        if measurement_date_from is not None:
            statement = statement.where(ReportChunk.measurement_date >= measurement_date_from)

        if measurement_date_to is not None:
            statement = statement.where(ReportChunk.measurement_date <= measurement_date_to)

        if chunk_types:
            statement = statement.where(ReportChunk.chunk_type.in_(chunk_types))

        statement = statement.order_by(distance.asc()).limit(limit)

        rows = self._session.execute(statement).all()

        return [
            {
                "report_chunk": row[0],
                "distance": float(row[1]),
            }
            for row in rows
        ]

    def delete_by_report_id(
        self,
        report_id: uuid.UUID,
    ):
        """レポートに属するチャンクを一括削除する。"""

        statement = delete(ReportChunk).where(ReportChunk.report_id == report_id)

        result = cast(
            CursorResult[Any],
            self._session.execute(statement),
        )
        return result.rowcount
