import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.src.workflows.nodes.report_nodes import ReportNodes


def make_nodes() -> ReportNodes:
    """依存関係をMock化したReportNodesを作成する。"""
    azure_service = Mock()
    azure_service.chat_deployment = "chat-model"
    azure_service.embedding_deployment = "embedding-model"
    nodes = ReportNodes(
        session=Mock(),
        azure_openai_service=azure_service,
    )
    nodes._file_repository = Mock()
    nodes._report_repository = Mock()
    nodes._vector_repository = Mock()
    return nodes


def make_anomaly(**overrides):
    """テスト用の異常測定値を作成する。"""
    anomaly = SimpleNamespace(
        row_number=4,
        measured_at="2026-09-01T10:00:02+09:00",
        value=3.0,
        threshold=2.5,
        excess_value=0.5,
    )
    anomaly.to_dict = Mock(
        return_value={
            "row_number": anomaly.row_number,
            "measured_at": anomaly.measured_at,
            "value": anomaly.value,
            "threshold": anomaly.threshold,
            "excess_value": anomaly.excess_value,
        }
    )
    for name, value in overrides.items():
        setattr(anomaly, name, value)
    return anomaly


def make_analysis_result(*, anomalies=None):
    """テスト用の振動分析結果を作成する。"""
    return SimpleNamespace(
        record_count=3,
        minimum_value=1.0,
        maximum_value=3.0,
        average_value=2.0,
        median_value=2.0,
        standard_deviation=0.816,
        threshold_value=2.5,
        anomaly_count=1 if anomalies else 0,
        anomaly_rate=1 / 3 if anomalies else 0.0,
        status="requires_attention" if anomalies else "normal",
        anomalies=anomalies or [],
    )


def make_uploaded_file():
    """テスト用のCSV管理情報を作成する。"""
    return SimpleNamespace(
        id=uuid.uuid4(),
        equipment_id="MOTOR-001",
        measurement_date=date(2026, 9, 1),
    )


def make_report(**overrides):
    """テスト用のReportを作成する。"""
    report = SimpleNamespace(
        id=uuid.uuid4(),
        equipment_id="MOTOR-001",
        measurement_date=date(2026, 9, 1),
        status="requires_attention",
        anomaly_count=1,
        maximum_value=3.0,
        threshold_value=2.5,
        prompt_version="v1",
    )
    for name, value in overrides.items():
        setattr(report, name, value)
    return report


AI_TEXT = """1. 分析概要
振動値の上昇を確認しました。
2. 判定根拠
閾値を超える測定値があります。
3. 推奨対応
設備を点検してください。"""


def test_build_report_content_returns_summary_recommendation_and_text() -> None:
    """AI分析結果からReport保存用の内容を作成する。"""
    nodes = make_nodes()
    uploaded_file = make_uploaded_file()
    analysis_result = make_analysis_result(anomalies=[make_anomaly()])

    result = nodes.build_report_content(
        {
            "uploaded_file": uploaded_file,
            "analysis_result": analysis_result,
            "ai_analysis_text": AI_TEXT,
            "weather": "晴れ",
        }
    )

    assert result["ai_summary"].startswith("1. 分析概要")
    assert result["recommendation"] == "設備を点検してください。"
    assert "対象設備: MOTOR-001" in result["report_text"]
    assert "天候: 晴れ" in result["report_text"]
    assert "異常測定値:" in result["report_text"]


def test_save_report_passes_analysis_data_to_repository() -> None:
    """分析結果とAI生成内容をRepositoryへ渡す。"""
    nodes = make_nodes()
    uploaded_file = make_uploaded_file()
    anomaly = make_anomaly()
    analysis_result = make_analysis_result(anomalies=[anomaly])
    saved_report = make_report()
    nodes._report_repository.create.return_value = saved_report
    created_by = uuid.uuid4()

    result = nodes.save_report(
        {
            "uploaded_file": uploaded_file,
            "analysis_result": analysis_result,
            "ai_analysis_text": AI_TEXT,
            "created_by": created_by,
            "weather": "晴れ",
            "ai_summary": "概要",
            "recommendation": "設備を点検してください。",
            "report_text": "本文",
        }
    )

    assert result == {"report": saved_report, "report_id": saved_report.id}
    call = nodes._report_repository.create.call_args.kwargs
    assert call["uploaded_file_id"] == uploaded_file.id
    assert call["created_by"] == created_by
    assert call["equipment_id"] == "MOTOR-001"
    assert call["anomaly_details"] == [anomaly.to_dict.return_value]
    assert call["ai_model"] == "chat-model"
    assert call["prompt_version"] == "v1"


def test_build_report_chunks_creates_five_semantic_chunks() -> None:
    """Reportを5種類のRAG検索用Chunkへ分割する。"""
    nodes = make_nodes()
    report = make_report()
    analysis_result = make_analysis_result(anomalies=[make_anomaly()])

    result = nodes.build_report_chunks(
        {
            "report": report,
            "analysis_result": analysis_result,
            "ai_analysis_text": AI_TEXT,
            "report_text": "レポート全文",
        }
    )

    chunks = result["report_chunks"]
    assert len(chunks) == 5
    assert [chunk["chunk_index"] for chunk in chunks] == [0, 1, 2, 3, 4]
    assert [chunk["chunk_type"] for chunk in chunks] == [
        "full_report",
        "analysis_summary",
        "judgment_reason",
        "recommendation",
        "anomaly_details",
    ]
    assert chunks[0]["content"] == "レポート全文"
    assert "振動値の上昇" in chunks[1]["content"]
    assert "閾値を超える" in chunks[2]["content"]
    assert "設備を点検" in chunks[3]["content"]
    assert "超過量=0.5" in chunks[4]["content"]
    assert chunks[0]["metadata_json"]["status"] == "requires_attention"


def test_build_report_chunks_handles_no_anomalies() -> None:
    """異常候補がない場合は固定文をChunkへ格納する。"""
    nodes = make_nodes()

    result = nodes.build_report_chunks(
        {
            "report": make_report(anomaly_count=0, status="normal"),
            "analysis_result": make_analysis_result(anomalies=[]),
            "ai_analysis_text": AI_TEXT,
            "report_text": "レポート全文",
        }
    )

    assert result["report_chunks"][4]["content"].endswith(
        "異常候補はありません。"
    )


def test_generate_chunk_embeddings_adds_model_and_dimensions() -> None:
    """各ChunkへEmbedding情報を追加する。"""
    nodes = make_nodes()
    chunks = [
        {
            "chunk_index": index,
            "chunk_type": chunk_type,
            "content": f"content-{index}",
            "metadata_json": {},
        }
        for index, chunk_type in enumerate(["full_report", "analysis_summary"])
    ]
    nodes._azure_openai_service.create_embedding.side_effect = [
        [0.1, 0.2],
        [0.3, 0.4],
    ]

    result = nodes.generate_chunk_embeddings({"report_chunks": chunks})

    assert len(result["embedded_report_chunks"]) == 2
    assert result["embedding"] == [0.1, 0.2]
    assert result["embedding_model"] == "embedding-model"
    assert result["embedding_dimensions"] == 2
    assert nodes._azure_openai_service.create_embedding.call_count == 2


def test_save_report_chunks_saves_all_chunks_and_returns_first() -> None:
    """Embedding済みChunkを保存し、full_report Chunkを返す。"""
    nodes = make_nodes()
    report = make_report()
    embedded_chunks = [
        {
            "chunk_index": index,
            "chunk_type": chunk_type,
            "content": f"content-{index}",
            "metadata_json": {"status": "normal"},
            "embedding": [0.1, 0.2],
            "embedding_model": "embedding-model",
            "embedding_dimensions": 2,
        }
        for index, chunk_type in enumerate(["full_report", "analysis_summary"])
    ]
    saved = [SimpleNamespace(id=uuid.uuid4()), SimpleNamespace(id=uuid.uuid4())]
    nodes._vector_repository.create.side_effect = saved

    result = nodes.save_report_chunks(
        {"report": report, "embedded_report_chunks": embedded_chunks}
    )

    assert result["report_chunk"] is saved[0]
    assert result["report_chunk_id"] == saved[0].id
    assert result["saved_report_chunks"] == saved
    assert nodes._vector_repository.create.call_count == 2
    first_call = nodes._vector_repository.create.call_args_list[0].kwargs
    assert first_call["report_id"] == report.id
    assert first_call["embedding_version"] == "1"
    assert first_call["equipment_id"] == "MOTOR-001"


def test_mark_completed_updates_uploaded_file_status() -> None:
    """CSV管理情報をcompletedへ更新する。"""
    nodes = make_nodes()
    uploaded_file = make_uploaded_file()
    updated_file = make_uploaded_file()
    nodes._file_repository.update_status.return_value = updated_file

    result = nodes.mark_completed({"uploaded_file": uploaded_file})

    assert result == {"uploaded_file": updated_file}
    nodes._file_repository.update_status.assert_called_once_with(
        uploaded_file,
        status="completed",
        error_code=None,
        error_message=None,
    )


def test_split_ai_analysis_parses_all_sections() -> None:
    """AI分析文を3つの見出しへ分割する。"""
    result = ReportNodes._split_ai_analysis(AI_TEXT)

    assert result == {
        "analysis_summary": "振動値の上昇を確認しました。",
        "judgment_reason": "閾値を超える測定値があります。",
        "recommendation": "設備を点検してください。",
    }


def test_split_ai_analysis_uses_full_text_without_markers() -> None:
    """見出しがない場合は全文を分析概要へ格納する。"""
    result = ReportNodes._split_ai_analysis("分析結果のみ")

    assert result["analysis_summary"] == "分析結果のみ"
    assert result["judgment_reason"] == "該当する記載はありません。"
    assert result["recommendation"] == "該当する記載はありません。"


def test_build_report_text_uses_unset_weather_and_no_anomaly_section() -> None:
    """天候未設定と異常なしを安全に本文へ反映する。"""
    result = ReportNodes._build_report_text(
        make_uploaded_file(),
        make_analysis_result(anomalies=[]),
        "AI分析",
        None,
    )

    assert "天候: 未設定" in result
    assert "AI分析:\nAI分析" in result
    assert "異常測定値:" not in result


@pytest.mark.parametrize(
    ("text", "expected"),
    [("  複数   空白  ", "複数 空白"), ("", "AI分析結果なし")],
)
def test_create_summary_normalizes_text(text: str, expected: str) -> None:
    """AI分析概要を正規化する。"""
    assert ReportNodes._create_summary(text) == expected


def test_create_summary_truncates_to_500_characters() -> None:
    """AI分析概要を500文字へ制限する。"""
    assert len(ReportNodes._create_summary("x" * 600)) == 500


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (AI_TEXT, "設備を点検してください。"),
        ("見出しなしの回答", "見出しなしの回答"),
        ("3. 推奨対応\n", "3. 推奨対応\n"),
    ],
)
def test_extract_recommendation(text: str, expected: str) -> None:
    """推奨対応部分を抽出する。"""
    assert ReportNodes._extract_recommendation(text) == expected
