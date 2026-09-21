import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.src.prompts.rag_chat_prompt import (
    NO_SEARCH_RESULTS_ANSWER,
    RAG_CHAT_INSTRUCTIONS,
    build_rag_chat_input,
)
from backend.src.workflows.graphs.rag_chat_graph import build_rag_chat_graph
from backend.src.workflows.nodes.rag_nodes import RagNodes, route_after_search


def make_state(**overrides) -> dict:
    """RAG Chat Node用の基本Stateを作成する。"""
    state = {
        "query": "MOTOR-001の異常原因は何ですか？",
        "limit": 5,
        "equipment_id": "MOTOR-001",
        "measurement_date_from": date(2026, 9, 1),
        "measurement_date_to": date(2026, 9, 30),
        "chunk_types": ["analysis_summary", "recommendation"],
        "search_results": [],
        "has_search_results": False,
        "context": "",
    }
    state.update(overrides)
    return state


def make_search_result(
    *,
    chunk_id=None,
    measurement_date=date(2026, 9, 1),
    metadata_json=None,
):
    """RagSearchServiceが返す検索結果を作成する。"""
    chunk = SimpleNamespace(
        id=chunk_id or uuid.uuid4(),
        report_id=uuid.uuid4(),
        chunk_index=1,
        chunk_type="analysis_summary",
        content="振動値の上昇を確認しました。",
        equipment_id="MOTOR-001",
        measurement_date=measurement_date,
        metadata_json=metadata_json,
    )
    return SimpleNamespace(
        report_chunk=chunk,
        distance=0.2,
        similarity=0.8,
    )


def make_chat_search_result(
    *,
    chunk_id=None,
    measurement_date=date(2026, 9, 1),
    similarity=0.8,
) -> dict:
    """Node間で共有する検索結果を作成する。"""
    return {
        "report_chunk_id": chunk_id or uuid.uuid4(),
        "report_id": uuid.uuid4(),
        "chunk_index": 1,
        "chunk_type": "analysis_summary",
        "content": "振動値の上昇を確認しました。",
        "equipment_id": "MOTOR-001",
        "measurement_date": measurement_date,
        "distance": 0.2,
        "similarity": similarity,
        "metadata_json": {},
    }


def test_search_report_chunks_converts_service_results() -> None:
    """検索Serviceの結果をChatState用の辞書へ変換する。"""
    rag_search_service = Mock()
    azure_service = Mock()
    raw_result = make_search_result(metadata_json=None)
    rag_search_service.search.return_value = [raw_result]
    nodes = RagNodes(
        session=Mock(),
        rag_search_service=rag_search_service,
        azure_openai_service=azure_service,
    )

    result = nodes.search_report_chunks(make_state())

    assert result["has_search_results"] is True
    assert len(result["search_results"]) == 1
    item = result["search_results"][0]
    assert item["report_chunk_id"] == raw_result.report_chunk.id
    assert item["report_id"] == raw_result.report_chunk.report_id
    assert item["distance"] == pytest.approx(0.2)
    assert item["similarity"] == pytest.approx(0.8)
    assert item["metadata_json"] == {}
    rag_search_service.search.assert_called_once_with(
        query="MOTOR-001の異常原因は何ですか？",
        limit=5,
        equipment_id="MOTOR-001",
        measurement_date_from=date(2026, 9, 1),
        measurement_date_to=date(2026, 9, 30),
        chunk_types=["analysis_summary", "recommendation"],
    )


def test_search_report_chunks_marks_empty_results() -> None:
    """検索結果がない場合はhas_search_resultsをFalseにする。"""
    rag_search_service = Mock()
    rag_search_service.search.return_value = []
    nodes = RagNodes(
        session=Mock(),
        rag_search_service=rag_search_service,
        azure_openai_service=Mock(),
    )

    result = nodes.search_report_chunks(make_state())

    assert result == {
        "search_results": [],
        "has_search_results": False,
    }


def test_build_context_formats_results() -> None:
    """検索結果を参照番号付きContextへ整形する。"""
    first = make_chat_search_result(similarity=0.81234567)
    second = make_chat_search_result(measurement_date=None, similarity=0.5)
    nodes = RagNodes(
        session=Mock(),
        rag_search_service=Mock(),
        azure_openai_service=Mock(),
    )

    result = nodes.build_context(make_state(search_results=[first, second]))

    context = result["context"]
    assert "[参照1]" in context
    assert "[参照2]" in context
    assert f"レポートID: {first['report_id']}" in context
    assert "測定日: 2026-09-01" in context
    assert "測定日: 未設定" in context
    assert "類似度: 0.812346" in context
    assert "内容:\n振動値の上昇を確認しました。" in context


def test_build_context_returns_empty_text_for_no_results() -> None:
    """検索結果がない場合は空Contextを返す。"""
    nodes = RagNodes(Mock(), Mock(), Mock())

    assert nodes.build_context(make_state(search_results=[])) == {"context": ""}


def test_generate_answer_calls_azure_openai() -> None:
    """Promptを組み立て、Azure OpenAIへ回答生成を依頼する。"""
    azure_service = Mock()
    azure_service.generate_text.return_value = "設備を点検してください。"
    nodes = RagNodes(
        session=Mock(),
        rag_search_service=Mock(),
        azure_openai_service=azure_service,
    )
    state = make_state(context="[参照1]\n内容: 振動値上昇")

    result = nodes.generate_answer(state)

    assert result == {"answer": "設備を点検してください。"}
    call = azure_service.generate_text.call_args.kwargs
    assert call["instructions"] == RAG_CHAT_INSTRUCTIONS
    assert "【質問】\nMOTOR-001の異常原因は何ですか？" in call["input_text"]
    assert "【過去レポート情報】\n[参照1]" in call["input_text"]
    assert call["max_output_tokens"] == 1000


def test_build_no_results_answer_returns_fixed_answer() -> None:
    """検索結果なしの場合は固定回答と空Sourceを返す。"""
    nodes = RagNodes(Mock(), Mock(), Mock())

    assert nodes.build_no_results_answer(make_state()) == {
        "answer": NO_SEARCH_RESULTS_ANSWER,
        "sources": [],
    }


def test_build_sources_removes_duplicate_chunk_ids() -> None:
    """同一Chunk IDの参照元を重複して返さない。"""
    shared_chunk_id = uuid.uuid4()
    first = make_chat_search_result(chunk_id=shared_chunk_id)
    duplicate = make_chat_search_result(chunk_id=shared_chunk_id)
    second = make_chat_search_result()
    nodes = RagNodes(Mock(), Mock(), Mock())

    result = nodes.build_sources(make_state(search_results=[first, duplicate, second]))

    assert len(result["sources"]) == 2
    assert [source["report_chunk_id"] for source in result["sources"]] == [
        shared_chunk_id,
        second["report_chunk_id"],
    ]
    assert "content" not in result["sources"][0]
    assert "distance" not in result["sources"][0]


@pytest.mark.parametrize(
    ("has_results", "expected"),
    [
        (True, "build_context"),
        (False, "build_no_results_answer"),
        (None, "build_no_results_answer"),
    ],
)
def test_route_after_search(has_results, expected: str) -> None:
    """検索結果の有無に応じて次のNodeを選択する。"""
    state = {} if has_results is None else {"has_search_results": has_results}

    assert route_after_search(state) == expected


def test_build_rag_chat_input_formats_query_and_context() -> None:
    """質問とContextを回答生成用入力へ整形する。"""
    result = build_rag_chat_input(query="質問", context="参照情報")

    assert "【質問】\n質問" in result
    assert "【過去レポート情報】\n参照情報" in result


def test_graph_runs_no_results_path() -> None:
    """Graphが検索結果なしの分岐を最後まで実行する。"""
    rag_search_service = Mock()
    rag_search_service.search.return_value = []
    azure_service = Mock()
    graph = build_rag_chat_graph(
        session=Mock(),
        rag_search_service=rag_search_service,
        azure_openai_service=azure_service,
    )

    result = graph.invoke(make_state())

    assert result == {
        "query": "MOTOR-001の異常原因は何ですか？",
        "answer": NO_SEARCH_RESULTS_ANSWER,
        "sources": [],
    }
    azure_service.generate_text.assert_not_called()


def test_graph_runs_search_results_path() -> None:
    """Graphが検索、Context、回答、Source生成を最後まで実行する。"""
    rag_search_service = Mock()
    raw_result = make_search_result()
    rag_search_service.search.return_value = [raw_result]
    azure_service = Mock()
    azure_service.generate_text.return_value = "振動値上昇が確認されています。"
    graph = build_rag_chat_graph(
        session=Mock(),
        rag_search_service=rag_search_service,
        azure_openai_service=azure_service,
    )

    result = graph.invoke(make_state())

    assert result["query"] == "MOTOR-001の異常原因は何ですか？"
    assert result["answer"] == "振動値上昇が確認されています。"
    assert len(result["sources"]) == 1
    assert result["sources"][0]["report_chunk_id"] == raw_result.report_chunk.id
    azure_service.generate_text.assert_called_once()
