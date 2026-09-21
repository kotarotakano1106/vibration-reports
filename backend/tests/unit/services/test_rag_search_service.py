from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.src.services.azure_openai_service import AzureOpenAIServiceError
from backend.src.services.rag_search_service import (
    DEFAULT_CHUNK_TYPES,
    RagSearchEmbeddingError,
    RagSearchQueryError,
    RagSearchService,
)


@pytest.fixture
def azure_service() -> Mock:
    service = Mock()
    service.create_embedding.return_value = [0.1, 0.2, 0.3]
    return service


@pytest.fixture
def service(azure_service: Mock) -> RagSearchService:
    instance = RagSearchService(
        session=Mock(),
        azure_openai_service=azure_service,
    )
    instance._vector_repository = Mock()
    return instance


def test_search_returns_converted_results(
    service: RagSearchService,
    azure_service: Mock,
) -> None:
    chunk = SimpleNamespace(id="chunk-id")
    service._vector_repository.search_similar.return_value = [
        {"report_chunk": chunk, "distance": 0.25}
    ]

    result = service.search("  異常振動  ")

    assert len(result) == 1
    assert result[0].report_chunk is chunk
    assert result[0].distance == pytest.approx(0.25)
    assert result[0].similarity == pytest.approx(0.75)
    azure_service.create_embedding.assert_called_once_with("異常振動")
    service._vector_repository.search_similar.assert_called_once_with(
        query_embedding=[0.1, 0.2, 0.3],
        limit=5,
        equipment_id=None,
        measurement_date_from=None,
        measurement_date_to=None,
        chunk_types=DEFAULT_CHUNK_TYPES,
    )


def test_search_passes_normalized_filters(service: RagSearchService) -> None:
    service._vector_repository.search_similar.return_value = []

    result = service.search(
        "  設備の状態  ",
        limit=10,
        equipment_id="  MOTOR-001  ",
        measurement_date_from=date(2026, 9, 1),
        measurement_date_to=date(2026, 9, 30),
        chunk_types=[
            " recommendation ",
            "analysis_summary",
            "recommendation",
            " ",
        ],
    )

    assert result == []
    service._vector_repository.search_similar.assert_called_once_with(
        query_embedding=[0.1, 0.2, 0.3],
        limit=10,
        equipment_id="MOTOR-001",
        measurement_date_from=date(2026, 9, 1),
        measurement_date_to=date(2026, 9, 30),
        chunk_types=["recommendation", "analysis_summary"],
    )


def test_search_converts_embedding_error(
    service: RagSearchService,
    azure_service: Mock,
) -> None:
    azure_service.create_embedding.side_effect = AzureOpenAIServiceError(
        "embedding failed"
    )

    with pytest.raises(RagSearchEmbeddingError) as exc_info:
        service.search("異常振動")

    assert isinstance(exc_info.value.__cause__, AzureOpenAIServiceError)
    service._vector_repository.search_similar.assert_not_called()


@pytest.mark.parametrize("query", [None, 123, "", "   ", "x" * 2001])
def test_search_rejects_invalid_query(
    service: RagSearchService,
    query: object,
) -> None:
    with pytest.raises(RagSearchQueryError):
        service.search(query)


@pytest.mark.parametrize("limit", [True, 1.5, "5", 0, 21])
def test_search_rejects_invalid_limit(
    service: RagSearchService,
    limit: object,
) -> None:
    with pytest.raises(RagSearchQueryError):
        service.search("異常振動", limit=limit)


@pytest.mark.parametrize("equipment_id", [123, [], {}])
def test_search_rejects_invalid_equipment_id(
    service: RagSearchService,
    equipment_id: object,
) -> None:
    with pytest.raises(RagSearchQueryError):
        service.search("異常振動", equipment_id=equipment_id)


def test_search_normalizes_blank_equipment_id_to_none(
    service: RagSearchService,
) -> None:
    service._vector_repository.search_similar.return_value = []

    service.search("異常振動", equipment_id="   ")

    assert (
        service._vector_repository.search_similar.call_args.kwargs[
            "equipment_id"
        ]
        is None
    )


@pytest.mark.parametrize(
    "chunk_types",
    ["analysis_summary", (), {}, [1], [None], [], [" "]],
)
def test_search_rejects_invalid_chunk_types(
    service: RagSearchService,
    chunk_types: object,
) -> None:
    with pytest.raises(RagSearchQueryError):
        service.search("異常振動", chunk_types=chunk_types)


@pytest.mark.parametrize(
    ("date_from", "date_to"),
    [
        ("2026-09-01", None),
        (None, "2026-09-30"),
        (date(2026, 9, 30), date(2026, 9, 1)),
    ],
)
def test_search_rejects_invalid_date_range(
    service: RagSearchService,
    date_from: object,
    date_to: object,
) -> None:
    with pytest.raises(RagSearchQueryError):
        service.search(
            "異常振動",
            measurement_date_from=date_from,
            measurement_date_to=date_to,
        )


@pytest.mark.parametrize(
    ("distance", "expected"),
    [
        (0.0, 1.0),
        (0.1234567, 0.876543),
        (1.0, 0.0),
        (1.5, 0.0),
        (-0.5, 1.0),
        ("0.2", 0.8),
    ],
)
def test_to_similarity_clamps_and_rounds(
    distance: object,
    expected: float,
) -> None:
    assert RagSearchService._to_similarity(distance) == expected
