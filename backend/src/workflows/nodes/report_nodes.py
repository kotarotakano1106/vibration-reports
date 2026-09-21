"""レポート・Embeddingの生成と保存を担当するLangGraph Node。"""

from backend.src.repositories.report_repository import (
    ReportRepository,
)
from backend.src.repositories.uploaded_file_repository import (
    UploadedFileRepository,
)
from backend.src.repositories.vector_repository import (
    VectorRepository,
)
from backend.src.services.azure_openai_service import (
    AzureOpenAIService,
)
from backend.src.workflows.states.analysis_state import (
    AnalysisState,
    EmbeddedReportChunkData,
    ReportChunkData,
)


class ReportNodes:
    """分析結果をレポートとEmbeddingとして保存するNode群。"""

    def __init__(
        self,
        session,
        azure_openai_service=None,
    ):
        self._file_repository = UploadedFileRepository(session)
        self._report_repository = ReportRepository(session)
        self._vector_repository = VectorRepository(session)
        self._azure_openai_service = (
            azure_openai_service
            if azure_openai_service is not None
            else AzureOpenAIService()
        )

    def build_report_content(self, state: AnalysisState) -> dict:
        """AI分析結果からレポート保存用の内容を作る。"""

        uploaded_file = state["uploaded_file"]
        analysis_result = state["analysis_result"]
        ai_analysis_text = state["ai_analysis_text"]

        report_text = self._build_report_text(
            uploaded_file=uploaded_file,
            analysis_result=analysis_result,
            ai_analysis_text=ai_analysis_text,
            weather=state["weather"],
        )

        return {
            "ai_summary": self._create_summary(ai_analysis_text),
            "recommendation": self._extract_recommendation(
                ai_analysis_text
            ),
            "report_text": report_text,
        }

    def save_report(self, state: AnalysisState) -> dict:
        """分析結果とAI生成内容をReportへ保存する。"""

        uploaded_file = state["uploaded_file"]
        analysis_result = state["analysis_result"]
        ai_analysis_text = state["ai_analysis_text"]
        anomaly_details = [
            anomaly.to_dict()
            for anomaly in analysis_result.anomalies
        ]

        report = self._report_repository.create(
            uploaded_file_id=uploaded_file.id,
            created_by=state["created_by"],
            equipment_id=uploaded_file.equipment_id,
            measurement_date=uploaded_file.measurement_date,
            weather=state["weather"],
            title=(
                f"{uploaded_file.equipment_id} 振動分析レポート"
            ),
            record_count=analysis_result.record_count,
            minimum_value=analysis_result.minimum_value,
            maximum_value=analysis_result.maximum_value,
            average_value=analysis_result.average_value,
            median_value=analysis_result.median_value,
            standard_deviation=analysis_result.standard_deviation,
            threshold_value=analysis_result.threshold_value,
            anomaly_count=analysis_result.anomaly_count,
            anomaly_details=anomaly_details,
            status=analysis_result.status,
            ai_summary=state["ai_summary"],
            ai_analysis=ai_analysis_text,
            recommendation=state["recommendation"],
            report_text=state["report_text"],
            ai_model=self._azure_openai_service.chat_deployment,
            prompt_version="v1",
        )

        return {"report": report, "report_id": report.id}

    def build_report_chunks(self, state: AnalysisState) -> dict:
        """レポートをRAG検索向けの意味単位へ分割する。"""

        report = state["report"]
        analysis_result = state["analysis_result"]
        sections = self._split_ai_analysis(
            state["ai_analysis_text"]
        )
        metadata = {
            "status": report.status,
            "anomaly_count": report.anomaly_count,
            "maximum_value": report.maximum_value,
            "threshold_value": report.threshold_value,
            "prompt_version": report.prompt_version,
        }

        anomaly_lines = [
            (
                f"測定日時={anomaly.measured_at}, "
                f"振動値={anomaly.value}, "
                f"閾値={anomaly.threshold}, "
                f"超過量={anomaly.excess_value}"
            )
            for anomaly in analysis_result.anomalies
        ]
        anomaly_content = (
            "\n".join(anomaly_lines)
            if anomaly_lines
            else "異常候補はありません。"
        )

        base_context = (
            f"設備ID: {report.equipment_id}\n"
            f"測定日: {report.measurement_date}\n"
        )

        chunks: list[ReportChunkData] = [
            {
                "chunk_index": 0,
                "chunk_type": "full_report",
                "content": state["report_text"],
                "metadata_json": metadata,
            },
            {
                "chunk_index": 1,
                "chunk_type": "analysis_summary",
                "content": base_context + sections["analysis_summary"],
                "metadata_json": metadata,
            },
            {
                "chunk_index": 2,
                "chunk_type": "judgment_reason",
                "content": base_context + sections["judgment_reason"],
                "metadata_json": metadata,
            },
            {
                "chunk_index": 3,
                "chunk_type": "recommendation",
                "content": base_context + sections["recommendation"],
                "metadata_json": metadata,
            },
            {
                "chunk_index": 4,
                "chunk_type": "anomaly_details",
                "content": base_context + anomaly_content,
                "metadata_json": metadata,
            },
        ]

        return {"report_chunks": chunks}

    def generate_chunk_embeddings(
        self,
        state: AnalysisState,
    ) -> dict:
        """各レポートチャンクのEmbeddingを生成する。"""

        model = self._azure_openai_service.embedding_deployment
        embedded_chunks: list[EmbeddedReportChunkData] = []

        for chunk in state["report_chunks"]:
            embedding = self._azure_openai_service.create_embedding(
                chunk["content"]
            )
            embedded_chunks.append(
                {
                    **chunk,
                    "embedding": embedding,
                    "embedding_model": model,
                    "embedding_dimensions": len(embedding),
                }
            )

        full_report = embedded_chunks[0]
        return {
            "embedded_report_chunks": embedded_chunks,
            "embedding": full_report["embedding"],
            "embedding_model": full_report["embedding_model"],
            "embedding_dimensions": full_report[
                "embedding_dimensions"
            ],
        }

    def save_report_chunks(self, state: AnalysisState) -> dict:
        """Embedding生成済みチャンクをDBへ保存する。"""

        report = state["report"]
        saved_chunks = []

        for chunk in state["embedded_report_chunks"]:
            saved_chunks.append(
                self._vector_repository.create(
                    report_id=report.id,
                    chunk_index=chunk["chunk_index"],
                    chunk_type=chunk["chunk_type"],
                    content=chunk["content"],
                    embedding=chunk["embedding"],
                    embedding_model=chunk["embedding_model"],
                    embedding_version="1",
                    equipment_id=report.equipment_id,
                    measurement_date=report.measurement_date,
                    metadata_json=chunk["metadata_json"],
                )
            )

        full_report_chunk = saved_chunks[0]
        return {
            "report_chunk": full_report_chunk,
            "report_chunk_id": full_report_chunk.id,
            "saved_report_chunks": saved_chunks,
        }

    def mark_completed(self, state: AnalysisState) -> dict:
        """CSV管理情報をcompletedへ更新する。"""

        uploaded_file = self._file_repository.update_status(
            state["uploaded_file"],
            status="completed",
            error_code=None,
            error_message=None,
        )
        return {"uploaded_file": uploaded_file}

    @staticmethod
    def _split_ai_analysis(text: str) -> dict[str, str]:
        """AI分析文を見出しごとの文章へ分割する。"""

        normalized = (
            text.replace("## ", "")
            .replace("<br>", "\n")
            .replace("<br/>", "\n")
            .replace("<br />", "\n")
        )
        markers = [
            ("1. 分析概要", "analysis_summary"),
            ("2. 判定根拠", "judgment_reason"),
            ("3. 推奨対応", "recommendation"),
        ]
        positions = [
            (normalized.find(marker), marker, key)
            for marker, key in markers
            if normalized.find(marker) >= 0
        ]
        positions.sort()

        sections = {
            "analysis_summary": "",
            "judgment_reason": "",
            "recommendation": "",
        }

        for index, (start, marker, key) in enumerate(positions):
            content_start = start + len(marker)
            content_end = (
                positions[index + 1][0]
                if index + 1 < len(positions)
                else len(normalized)
            )
            sections[key] = normalized[
                content_start:content_end
            ].strip()

        if not positions:
            sections["analysis_summary"] = normalized.strip()

        for key, value in sections.items():
            if not value:
                sections[key] = "該当する記載はありません。"

        return sections

    @staticmethod
    def _build_report_text(
        uploaded_file,
        analysis_result,
        ai_analysis_text,
        weather,
    ) -> str:
        """DB保存・Embedding生成用レポート本文を作る。"""

        lines = [
            f"対象設備: {uploaded_file.equipment_id}",
            f"測定日: {uploaded_file.measurement_date}",
            f"天候: {weather or '未設定'}",
            f"測定件数: {analysis_result.record_count}",
            f"最小振動値: {analysis_result.minimum_value}",
            f"最大振動値: {analysis_result.maximum_value}",
            f"平均振動値: {analysis_result.average_value}",
            f"中央値: {analysis_result.median_value}",
            f"標準偏差: {analysis_result.standard_deviation}",
            f"閾値: {analysis_result.threshold_value}",
            f"異常件数: {analysis_result.anomaly_count}",
            f"異常率: {analysis_result.anomaly_rate}",
            f"判定: {analysis_result.status}",
            "",
            "AI分析:",
            ai_analysis_text,
        ]

        if analysis_result.anomalies:
            lines.extend(["", "異常測定値:"])
            for anomaly in analysis_result.anomalies:
                lines.append(
                    f"行{anomaly.row_number}: "
                    f"{anomaly.measured_at}, "
                    f"振動値={anomaly.value}, "
                    f"閾値={anomaly.threshold}, "
                    f"超過量={anomaly.excess_value}"
                )

        return "\n".join(lines)

    @staticmethod
    def _create_summary(ai_analysis_text: str) -> str:
        normalized_text = " ".join(ai_analysis_text.split())
        return normalized_text[:500] or "AI分析結果なし"

    @staticmethod
    def _extract_recommendation(ai_analysis_text: str) -> str:
        marker = "3. 推奨対応"
        if marker not in ai_analysis_text:
            return ai_analysis_text[:1000]
        recommendation = ai_analysis_text.split(marker, 1)[1].strip()
        return (recommendation or ai_analysis_text)[:1000]
