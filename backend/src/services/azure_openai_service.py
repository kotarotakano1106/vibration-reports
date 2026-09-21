import os
from pathlib import Path

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"

EXPECTED_EMBEDDING_DIMENSIONS = 1536


class AzureOpenAIServiceError(Exception):
    """Azure OpenAI Service共通エラー。"""


class AzureOpenAIAuthenticationError(
    AzureOpenAIServiceError
):
    """Azure OpenAIの認証エラー。"""


class AzureOpenAIConnectionError(
    AzureOpenAIServiceError
):
    """Azure OpenAIへの接続エラー。"""


class AzureOpenAIRateLimitError(
    AzureOpenAIServiceError
):
    """Azure OpenAIのレート制限エラー。"""


class AzureOpenAIResponseError(
    AzureOpenAIServiceError
):
    """Azure OpenAIの応答エラー。"""


class EmbeddingDimensionError(
    AzureOpenAIServiceError
):
    """Embedding次元数不一致エラー。"""


def get_required_environment_value(name):
    """必須環境変数を取得する。"""

    value = os.getenv(name)

    if not value:
        raise AzureOpenAIServiceError(
            f"環境変数 {name} が設定されていません。"
        )

    return value.strip()


class AzureOpenAIService:
    """Azure OpenAIのChatとEmbeddingを担当するService。"""

    def __init__(self):
        load_dotenv(
            dotenv_path=ENV_FILE,
            encoding="utf-8-sig",
            override=True,
        )

        chat_endpoint = get_required_environment_value(
            "AZURE_OPENAI_ENDPOINT"
        )

        chat_api_key = get_required_environment_value(
            "AZURE_OPENAI_API_KEY"
        )

        self._chat_deployment = (
            get_required_environment_value(
                "AZURE_OPENAI_CHAT_DEPLOYMENT"
            )
        )

        embedding_endpoint = (
            get_required_environment_value(
                "AZURE_OPENAI_EMBEDDING_ENDPOINT"
            )
        )

        embedding_api_key = (
            get_required_environment_value(
                "AZURE_OPENAI_EMBEDDING_API_KEY"
            )
        )

        self._embedding_deployment = (
            get_required_environment_value(
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
            )
        )

        chat_base_url = (
            f"{chat_endpoint.rstrip('/')}/openai/v1/"
        )

        embedding_base_url = (
            f"{embedding_endpoint.rstrip('/')}/openai/v1/"
        )

        self._chat_client = OpenAI(
            api_key=chat_api_key,
            base_url=chat_base_url,
            timeout=30.0,
            max_retries=2,
        )

        self._embedding_client = OpenAI(
            api_key=embedding_api_key,
            base_url=embedding_base_url,
            timeout=30.0,
            max_retries=2,
        )

    @property
    def chat_deployment(self):
        """Chatモデルのデプロイ名を返す。"""

        return self._chat_deployment

    @property
    def embedding_deployment(self):
        """Embeddingモデルのデプロイ名を返す。"""

        return self._embedding_deployment

    def generate_text(
        self,
        *,
        instructions,
        input_text,
        max_output_tokens=1000,
    ):
        """Chatモデルから文章を生成する。"""

        if not instructions.strip():
            raise ValueError(
                "instructionsを空にできません。"
            )

        if not input_text.strip():
            raise ValueError(
                "input_textを空にできません。"
            )

        try:
            response = self._chat_client.responses.create(
                model=self._chat_deployment,
                instructions=instructions,
                input=input_text,
                max_output_tokens=max_output_tokens,
            )

        except AuthenticationError as exc:
            raise AzureOpenAIAuthenticationError(
                "Chatモデルの認証に失敗しました。"
            ) from exc

        except RateLimitError as exc:
            raise AzureOpenAIRateLimitError(
                "Chatモデルのレート制限に達しました。"
            ) from exc

        except APIConnectionError as exc:
            raise AzureOpenAIConnectionError(
                "Chatモデルへ接続できませんでした。"
            ) from exc

        except APIStatusError as exc:
            raise AzureOpenAIResponseError(
                "ChatモデルからAPIエラーが返されました。"
                f" status_code={exc.status_code}"
            ) from exc

        output_text = response.output_text.strip()

        if not output_text:
            raise AzureOpenAIResponseError(
                "Chatモデルから空の応答が返されました。"
            )

        return output_text

    def generate_vibration_analysis(
        self,
        *,
        equipment_id,
        measurement_date,
        record_count,
        minimum_value,
        maximum_value,
        average_value,
        median_value,
        standard_deviation,
        threshold_value,
        anomaly_count,
    ):
        """振動統計情報からAI分析文章を生成する。"""

        instructions = (
            "あなたは設備保全を支援する分析アシスタントです。"
            "提示された振動統計情報だけを使用してください。"
            "数値を変更したり、存在しない測定結果を"
            "追加したりしないでください。"
            "回答は日本語で、次の見出しを使用してください。"
            "\n1. 分析概要"
            "\n2. 判定根拠"
            "\n3. 推奨対応"
        )

        input_text = (
            f"対象設備: {equipment_id}\n"
            f"測定日: {measurement_date}\n"
            f"測定件数: {record_count}\n"
            f"最小値: {minimum_value}\n"
            f"最大値: {maximum_value}\n"
            f"平均値: {average_value}\n"
            f"中央値: {median_value}\n"
            f"標準偏差: {standard_deviation}\n"
            f"閾値: {threshold_value}\n"
            f"異常件数: {anomaly_count}\n"
        )

        return self.generate_text(
            instructions=instructions,
            input_text=input_text,
            max_output_tokens=800,
        )

    def create_embedding(self, text):
        """文章からEmbeddingを生成する。"""

        if not text.strip():
            raise ValueError(
                "Embedding対象テキストを空にできません。"
            )

        try:
            response = (
                self._embedding_client.embeddings.create(
                    model=self._embedding_deployment,
                    input=text,
                )
            )

        except AuthenticationError as exc:
            raise AzureOpenAIAuthenticationError(
                "Embeddingモデルの認証に失敗しました。"
            ) from exc

        except RateLimitError as exc:
            raise AzureOpenAIRateLimitError(
                "Embeddingモデルの"
                "レート制限に達しました。"
            ) from exc

        except APIConnectionError as exc:
            raise AzureOpenAIConnectionError(
                "Embeddingモデルへ"
                "接続できませんでした。"
            ) from exc

        except APIStatusError as exc:
            raise AzureOpenAIResponseError(
                "Embeddingモデルから"
                "APIエラーが返されました。"
                f" status_code={exc.status_code}"
            ) from exc

        if not response.data:
            raise AzureOpenAIResponseError(
                "Embeddingデータが返されませんでした。"
            )

        embedding = response.data[0].embedding

        if not embedding:
            raise AzureOpenAIResponseError(
                "Embeddingベクトルが空です。"
            )

        dimensions = len(embedding)

        if dimensions != EXPECTED_EMBEDDING_DIMENSIONS:
            raise EmbeddingDimensionError(
                "Embedding次元数がDB定義と一致しません。"
                f" expected={EXPECTED_EMBEDDING_DIMENSIONS}"
                f" actual={dimensions}"
            )

        return embedding