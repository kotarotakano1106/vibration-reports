import uuid
from datetime import date
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import backend.src.api.v1.chat as chat_module
from backend.src.services.azure_openai_service import AzureOpenAIServiceError
from backend.src.services.rag_search_service import (
    RagSearchEmbeddingError,
    RagSearchQueryError,
    RagSearchServiceError,
)


def make_graph_result() -> dict:
    """APIレスポンスへ変換可能なGraph結果を作成する。"""
    return {
        "query": "MOTOR-001の異常原因は何ですか？",
        "answer": "過去レポートでは振動値の上昇が確認されています。",
        "sources": [
            {
                "report_chunk_id": uuid.uuid4(),
                "report_id": uuid.uuid4(),
                "chunk_type": "analysis_summary",
                "equipment_id": "MOTOR-001",
                "measurement_date": date(2026, 9, 1),
                "similarity": 0.85,
            }
        ],
    }


def install_graph_mock(
    monkeypatch: pytest.MonkeyPatch,
    *,
    result: dict | None = None,
    error: Exception | None = None,
) -> tuple[Mock, Mock]:
    """APIが生成するRAG Chat GraphをMockへ差し替える。"""
    graph = Mock()
    if error is not None:
        graph.invoke.side_effect = error
    else:
        graph.invoke.return_value = result or {
            "query": "質問",
            "answer": "回答",
            "sources": [],
        }

    factory = Mock(return_value=graph)
    monkeypatch.setattr(
        chat_module,
        "build_rag_chat_graph",
        factory,
    )
    return graph, factory


def test_chat_returns_answer_without_sources(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """参照元がない場合も回答を返す。"""
    graph, _ = install_graph_mock(
        monkeypatch,
        result={
            "query": "異常はありますか？",
            "answer": "参照できる過去レポートはありません。",
            "sources": [],
        },
    )

    response = api_client.post(
        "/api/v1/chat",
        json={"query": "異常はありますか？"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "query": "異常はありますか？",
        "answer": "参照できる過去レポートはありません。",
        "source_count": 0,
        "sources": [],
    }
    graph.invoke.assert_called_once()


def test_chat_returns_answer_and_source_schema(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """回答と根拠となるSource情報を返す。"""
    graph_result = make_graph_result()
    install_graph_mock(monkeypatch, result=graph_result)

    response = api_client.post(
        "/api/v1/chat",
        json={"query": "MOTOR-001の異常原因は何ですか？"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == graph_result["query"]
    assert body["answer"] == graph_result["answer"]
    assert body["source_count"] == 1

    source = body["sources"][0]
    expected = graph_result["sources"][0]
    assert source["report_chunk_id"] == str(expected["report_chunk_id"])
    assert source["report_id"] == str(expected["report_id"])
    assert source["chunk_type"] == "analysis_summary"
    assert source["equipment_id"] == "MOTOR-001"
    assert source["measurement_date"] == "2026-09-01"
    assert source["similarity"] == pytest.approx(0.85)


def test_chat_normalizes_and_passes_graph_input(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    db_session,
) -> None:
    """質問と検索条件を正規化してGraphへ渡す。"""
    graph, factory = install_graph_mock(
        monkeypatch,
        result={
            "query": "異常原因",
            "answer": "回答",
            "sources": [],
        },
    )

    response = api_client.post(
        "/api/v1/chat",
        json={
            "query": "  異常原因  ",
            "limit": 10,
            "equipment_id": "  MOTOR-001  ",
            "measurement_date_from": "2026-09-01",
            "measurement_date_to": "2026-09-30",
            "chunk_types": [
                " recommendation ",
                "analysis_summary",
                "recommendation",
                " ",
            ],
        },
    )

    assert response.status_code == 200
    factory.assert_called_once_with(session=db_session)
    graph.invoke.assert_called_once_with(
        {
            "query": "異常原因",
            "limit": 10,
            "equipment_id": "MOTOR-001",
            "measurement_date_from": date(2026, 9, 1),
            "measurement_date_to": date(2026, 9, 30),
            "chunk_types": ["recommendation", "analysis_summary"],
        }
    )


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (RagSearchQueryError("質問が不正です。"), 400),
        (RagSearchEmbeddingError("Embedding生成失敗"), 502),
        (AzureOpenAIServiceError("AI回答生成失敗"), 502),
        (RagSearchServiceError("検索処理失敗"), 500),
    ],
)
def test_chat_maps_graph_errors(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    expected_status: int,
) -> None:
    """Graph処理の例外を所定のHTTP Statusへ変換する。"""
    install_graph_mock(monkeypatch, error=error)

    response = api_client.post(
        "/api/v1/chat",
        json={"query": "異常原因"},
    )

    assert response.status_code == expected_status
    assert response.json()["detail"] == str(error)


@pytest.mark.parametrize(
    "payload",
    [
        {"query": ""},
        {"query": "   "},
        {"query": "異常", "limit": 0},
        {"query": "異常", "limit": 21},
        {
            "query": "異常",
            "measurement_date_from": "2026-09-30",
            "measurement_date_to": "2026-09-01",
        },
        {"query": "異常", "chunk_types": []},
        {"query": "異常", "chunk_types": [" "]},
        {"query": "x" * 2001},
        {"query": "異常", "equipment_id": "M" * 101},
    ],
)
def test_chat_rejects_invalid_request(
    api_client: TestClient,
    payload: dict,
) -> None:
    """不正な質問・検索条件では422を返す。"""
    response = api_client.post(
        "/api/v1/chat",
        json=payload,
    )

    assert response.status_code == 422
