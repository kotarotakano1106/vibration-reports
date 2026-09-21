import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.src.models.report import Report
from backend.src.models.uploaded_file import UploadedFile


class ReportRepository:
    """reportsテーブルへのDB操作を担当するRepository。"""

    def __init__(self, session: Session):
        self._session = session

    def create(
        self,
        *,
        uploaded_file_id: uuid.UUID,
        created_by: uuid.UUID,
        equipment_id: str,
        title: str,
        record_count: int,
        minimum_value: float,
        maximum_value: float,
        average_value: float,
        anomaly_count: int,
        anomaly_details: list[dict[str, Any]],
        status: str,
        ai_summary: str,
        ai_analysis: str,
        report_text: str,
        measurement_date: date | None = None,
        weather: str | None = None,
        median_value: float | None = None,
        standard_deviation: float | None = None,
        threshold_value: float | None = None,
        recommendation: str | None = None,
        ai_model: str | None = None,
        prompt_version: str | None = None,
        chart_path: str | None = None,
        pdf_path: str | None = None,
        pdf_generated_at: datetime | None = None,
    ):
        """分析レポートをSessionへ追加する。"""

        report = Report(
            uploaded_file_id=uploaded_file_id,
            created_by=created_by,
            equipment_id=equipment_id,
            measurement_date=measurement_date,
            weather=weather,
            title=title,
            record_count=record_count,
            minimum_value=minimum_value,
            maximum_value=maximum_value,
            average_value=average_value,
            median_value=median_value,
            standard_deviation=standard_deviation,
            threshold_value=threshold_value,
            anomaly_count=anomaly_count,
            anomaly_details=anomaly_details,
            status=status,
            ai_summary=ai_summary,
            ai_analysis=ai_analysis,
            recommendation=recommendation,
            report_text=report_text,
            ai_model=ai_model,
            prompt_version=prompt_version,
            chart_path=chart_path,
            pdf_path=pdf_path,
            pdf_generated_at=pdf_generated_at,
        )

        self._session.add(report)
        self._session.flush()
        self._session.refresh(report)

        return report

    def get_by_id(
        self,
        report_id: uuid.UUID,
    ):
        """UUIDでレポートを取得する。"""

        return self._session.get(
            Report,
            report_id,
        )

    def get_by_uploaded_file_id(
        self,
        uploaded_file_id: uuid.UUID,
    ):
        """アップロードファイルIDでレポートを取得する。"""

        statement = select(Report).where(
            Report.uploaded_file_id == uploaded_file_id
        )

        return self._session.scalar(statement)

    def list_by_equipment_id(
        self,
        equipment_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ):
        """設備IDに紐づくレポート一覧を取得する。"""

        statement = (
            select(Report)
            .where(
                Report.equipment_id == equipment_id
            )
            .order_by(
                Report.created_at.desc()
            )
            .offset(offset)
            .limit(limit)
        )

        return list(
            self._session.scalars(statement).all()
        )

    def list_all_with_files(self, *, limit: int = 100, offset: int = 0):
        """保存済みレポートと元CSVを新しい順で取得する。"""
        statement = (
            select(Report, UploadedFile)
            .join(UploadedFile, UploadedFile.id == Report.uploaded_file_id)
            .order_by(Report.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self._session.execute(statement).all())

    def update_pdf_information(
        self,
        report: Report,
        *,
        pdf_path: str,
        pdf_generated_at: datetime,
    ):
        """PDFの保存先と生成日時を更新する。"""

        report.pdf_path = pdf_path
        report.pdf_generated_at = pdf_generated_at
        report.updated_at = datetime.now().astimezone()

        self._session.flush()
        self._session.refresh(report)

        return report

    def delete(
        self,
        report: Report,
    ):
        """レポートをSessionから削除する。"""

        self._session.delete(report)
        self._session.flush()