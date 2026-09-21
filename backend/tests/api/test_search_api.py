import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import backend.src.api.v1.search as search_module
from backend.src.services.rag_search_service import (
    RagSearchEmbeddingError,
    RagSearchQueryError,
    RagSearchServiceError,
)


def make_search_result():
    """APIレスポンスへ変換可能な検索結果を作成する。"""
    chunk = SimpleNamespace(
        id=uuid.uuid4(),
        report_id=uuid.uuid4(),
        chunk_index=1,
        chunk_type="analysis_summary",
        content="振動値の上昇を確認しました。",
        equipment_id="MOTOR-001",
        measurement_date=date(2026, 9, 1),
        embedding_model="test-embedding-model",
        metadata_json={"source": "integration-test"},
    )
    return SimpleNamespace(
        report_chunk=chunk,
        distance=0.2,
        similarity=0.8,
    )


def install_search_service_mock(
    monkeypatch: pytest.MonkeyPatch,
    *,
    results=None,
    error: Exception | None = None,
) -> tuple[Mock, Mock]:
    """APIが生成するRagSearchServiceをMockへ差し替える。"""
    service = Mock()
    if error is not None:
        service.search.side_effect = error
    else:
        service.search.return_value = results or []

    factory = Mock(return_value=service)
    monkeypatch.setattr(
        search_module,
        "RagSearchService",
        factory,
    )
    return service, factory


def test_search_returns_empty_results(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """該当データがない場合は空の検索結果を返す。"""
    service, _ = install_search_service_mock(
        monkeypatch,
        results=[],
    )

    response = api_client.post(
        "/api/v1/search",
        json={"query": "異常振動"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "query": "異常振動",
        "result_count": 0,
        "results": [],
    }
    service.search.assert_called_once_with(
        query="異常振動",
        limit=5,
        equipment_id=None,
        measurement_date_from=None,
        measurement_date_to=None,
        chunk_types=[
            "analysis_summary",
            "judgment_reason",
            "recommendation",
            "anomaly_details",
        ],
    )


def test_search_returns_result_schema(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """類似検索結果をResponse Schemaへ変換する。"""
    result = make_search_result()
    install_search_service_mock(
        monkeypatch,
        results=[result],
    )

    response = api_client.post(
        "/api/v1/search",
        json={"query": "異常振動"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result_count"] == 1
    item = body["results"][0]
    chunk = result.report_chunk
    assert item["report_chunk_id"] == str(chunk.id)
    assert item["report_id"] == str(chunk.report_id)
    assert item["chunk_index"] == 1
    assert item["chunk_type"] == "analysis_summary"
    assert item["content"] == "振動値の上昇を確認しました。"
    assert item["equipment_id"] == "MOTOR-001"
    assert item["measurement_date"] == "2026-09-01"
    assert item["distance"] == pytest.approx(0.2)
    assert item["similarity"] == pytest.approx(0.8)
    assert item["embedding_model"] == "test-embedding-model"
    assert item["metadata_json"] == {"source": "integration-test"}


def test_search_normalizes_and_passes_filters(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """検索条件を正規化してServiceへ渡す。"""
    service, factory = install_search_service_mock(
        monkeypatch,
        results=[],
    )

    response = api_client.post(
        "/api/v1/search",
        json={
            "query": "  異常振動  ",
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
    assert response.json()["query"] == "異常振動"
    service.search.assert_called_once_with(
        query="異常振動",
        limit=10,
        equipment_id="MOTOR-001",
        measurement_date_from=date(2026, 9, 1),
        measurement_date_to=date(2026, 9, 30),
        chunk_types=["recommendation", "analysis_summary"],
    )
    factory.assert_called_once()


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (RagSearchQueryError("検索文が不正です。"), 400),
        (RagSearchEmbeddingError("Embedding生成失敗"), 502),
        (RagSearchServiceError("検索処理失敗"), 500),
    ],
)
def test_search_maps_service_errors(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    expected_status: int,
) -> None:
    """Service例外を所定のHTTP Statusへ変換する。"""
    install_search_service_mock(
        monkeypatch,
        error=error,
    )

    response = api_client.post(
        "/api/v1/search",
        json={"query": "異常振動"},
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
def test_search_rejects_invalid_request(
    api_client: TestClient,
    payload: dict,
) -> None:
    """不正な検索条件では422を返す。"""
    response = api_client.post(
        "/api/v1/search",
        json=payload,
    )

    assert response.status_code == 422
