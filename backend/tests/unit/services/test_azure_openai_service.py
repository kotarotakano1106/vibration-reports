from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    RateLimitError,
)

import backend.src.services.azure_openai_service as service_module
from backend.src.services.azure_openai_service import (
    EXPECTED_EMBEDDING_DIMENSIONS,
    AzureOpenAIAuthenticationError,
    AzureOpenAIConnectionError,
    AzureOpenAIRateLimitError,
    AzureOpenAIResponseError,
    AzureOpenAIService,
    AzureOpenAIServiceError,
    EmbeddingDimensionError,
    get_required_environment_value,
)


@pytest.fixture
def service() -> AzureOpenAIService:
    """初期化時の外部設定読込を避けたServiceを作成する。"""
    instance = AzureOpenAIService.__new__(AzureOpenAIService)
    instance._chat_deployment = "chat-deployment"
    instance._embedding_deployment = "embedding-deployment"
    instance._chat_client = Mock()
    instance._embedding_client = Mock()
    return instance


def make_status_error(status_code: int = 503) -> APIStatusError:
    """OpenAI APIStatusErrorを作成する。"""
    response = Mock()
    response.status_code = status_code
    response.request = Mock()
    return APIStatusError(
        "api status error",
        response=response,
        body=None,
    )


def test_get_required_environment_value_returns_stripped_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_REQUIRED_VALUE", "  value  ")

    assert get_required_environment_value("TEST_REQUIRED_VALUE") == "value"


@pytest.mark.parametrize("value", [None, ""])
def test_get_required_environment_value_rejects_missing_value(
    monkeypatch: pytest.MonkeyPatch,
    value: str | None,
) -> None:
    if value is None:
        monkeypatch.delenv("TEST_REQUIRED_VALUE", raising=False)
    else:
        monkeypatch.setenv("TEST_REQUIRED_VALUE", value)

    with pytest.raises(AzureOpenAIServiceError):
        get_required_environment_value("TEST_REQUIRED_VALUE")


def test_init_builds_separate_clients(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = {
        "AZURE_OPENAI_ENDPOINT": "https://chat.example/",
        "AZURE_OPENAI_API_KEY": "chat-key",
        "AZURE_OPENAI_CHAT_DEPLOYMENT": "chat-model",
        "AZURE_OPENAI_EMBEDDING_ENDPOINT": "https://embedding.example/",
        "AZURE_OPENAI_EMBEDDING_API_KEY": "embedding-key",
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "embedding-model",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)

    load_dotenv = Mock()
    openai_factory = Mock(side_effect=[Mock(), Mock()])
    monkeypatch.setattr(service_module, "load_dotenv", load_dotenv)
    monkeypatch.setattr(service_module, "OpenAI", openai_factory)

    instance = AzureOpenAIService()

    assert instance.chat_deployment == "chat-model"
    assert instance.embedding_deployment == "embedding-model"
    load_dotenv.assert_called_once()
    assert openai_factory.call_count == 2
    assert openai_factory.call_args_list[0].kwargs == {
        "api_key": "chat-key",
        "base_url": "https://chat.example/openai/v1/",
        "timeout": 30.0,
        "max_retries": 2,
    }
    assert openai_factory.call_args_list[1].kwargs == {
        "api_key": "embedding-key",
        "base_url": "https://embedding.example/openai/v1/",
        "timeout": 30.0,
        "max_retries": 2,
    }


def test_generate_text_returns_stripped_output(
    service: AzureOpenAIService,
) -> None:
    service._chat_client.responses.create.return_value = SimpleNamespace(
        output_text="  分析結果  "
    )

    result = service.generate_text(
        instructions="指示",
        input_text="入力",
        max_output_tokens=500,
    )

    assert result == "分析結果"
    service._chat_client.responses.create.assert_called_once_with(
        model="chat-deployment",
        instructions="指示",
        input="入力",
        max_output_tokens=500,
    )


@pytest.mark.parametrize(
    ("instructions", "input_text"),
    [("", "入力"), ("   ", "入力"), ("指示", ""), ("指示", "   ")],
)
def test_generate_text_rejects_blank_input(
    service: AzureOpenAIService,
    instructions: str,
    input_text: str,
) -> None:
    with pytest.raises(ValueError):
        service.generate_text(
            instructions=instructions,
            input_text=input_text,
        )


@pytest.mark.parametrize(
    ("error", "expected_exception"),
    [
        (AuthenticationError("auth", response=Mock(), body=None), AzureOpenAIAuthenticationError),
        (RateLimitError("rate", response=Mock(), body=None), AzureOpenAIRateLimitError),
        (APIConnectionError(request=Mock()), AzureOpenAIConnectionError),
        (make_status_error(503), AzureOpenAIResponseError),
    ],
)
def test_generate_text_converts_openai_errors(
    service: AzureOpenAIService,
    error: Exception,
    expected_exception: type[Exception],
) -> None:
    service._chat_client.responses.create.side_effect = error

    with pytest.raises(expected_exception) as exc_info:
        service.generate_text(instructions="指示", input_text="入力")

    assert exc_info.value.__cause__ is error


def test_generate_text_rejects_empty_response(
    service: AzureOpenAIService,
) -> None:
    service._chat_client.responses.create.return_value = SimpleNamespace(
        output_text="   "
    )

    with pytest.raises(AzureOpenAIResponseError):
        service.generate_text(instructions="指示", input_text="入力")


def test_generate_vibration_analysis_builds_prompt(
    service: AzureOpenAIService,
) -> None:
    service.generate_text = Mock(return_value="AI分析結果")

    result = service.generate_vibration_analysis(
        equipment_id="MOTOR-001",
        measurement_date="2026-09-01",
        record_count=3,
        minimum_value=1.0,
        maximum_value=3.0,
        average_value=2.0,
        median_value=2.0,
        standard_deviation=0.8,
        threshold_value=2.5,
        anomaly_count=1,
    )

    assert result == "AI分析結果"
    call = service.generate_text.call_args.kwargs
    assert "対象設備: MOTOR-001" in call["input_text"]
    assert "測定件数: 3" in call["input_text"]
    assert "閾値: 2.5" in call["input_text"]
    assert "異常件数: 1" in call["input_text"]
    assert call["max_output_tokens"] == 800


def test_create_embedding_returns_vector(
    service: AzureOpenAIService,
) -> None:
    embedding = [0.0] * EXPECTED_EMBEDDING_DIMENSIONS
    service._embedding_client.embeddings.create.return_value = SimpleNamespace(
        data=[SimpleNamespace(embedding=embedding)]
    )

    result = service.create_embedding("振動分析")

    assert result is embedding
    service._embedding_client.embeddings.create.assert_called_once_with(
        model="embedding-deployment",
        input="振動分析",
    )


@pytest.mark.parametrize("text", ["", "   "])
def test_create_embedding_rejects_blank_text(
    service: AzureOpenAIService,
    text: str,
) -> None:
    with pytest.raises(ValueError):
        service.create_embedding(text)


@pytest.mark.parametrize(
    ("error", "expected_exception"),
    [
        (AuthenticationError("auth", response=Mock(), body=None), AzureOpenAIAuthenticationError),
        (RateLimitError("rate", response=Mock(), body=None), AzureOpenAIRateLimitError),
        (APIConnectionError(request=Mock()), AzureOpenAIConnectionError),
        (make_status_error(500), AzureOpenAIResponseError),
    ],
)
def test_create_embedding_converts_openai_errors(
    service: AzureOpenAIService,
    error: Exception,
    expected_exception: type[Exception],
) -> None:
    service._embedding_client.embeddings.create.side_effect = error

    with pytest.raises(expected_exception) as exc_info:
        service.create_embedding("振動分析")

    assert exc_info.value.__cause__ is error


def test_create_embedding_rejects_missing_data(
    service: AzureOpenAIService,
) -> None:
    service._embedding_client.embeddings.create.return_value = SimpleNamespace(
        data=[]
    )

    with pytest.raises(AzureOpenAIResponseError):
        service.create_embedding("振動分析")


def test_create_embedding_rejects_empty_vector(
    service: AzureOpenAIService,
) -> None:
    service._embedding_client.embeddings.create.return_value = SimpleNamespace(
        data=[SimpleNamespace(embedding=[])]
    )

    with pytest.raises(AzureOpenAIResponseError):
        service.create_embedding("振動分析")


def test_create_embedding_rejects_unexpected_dimensions(
    service: AzureOpenAIService,
) -> None:
    service._embedding_client.embeddings.create.return_value = SimpleNamespace(
        data=[SimpleNamespace(embedding=[0.0] * 10)]
    )

    with pytest.raises(EmbeddingDimensionError) as exc_info:
        service.create_embedding("振動分析")

    assert "expected=1536" in str(exc_info.value)
    assert "actual=10" in str(exc_info.value)
