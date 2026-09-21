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


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

EXPECTED_EMBEDDING_DIMENSIONS = 1536


def get_required_environment_variable(name: str) -> str:
    """必須環境変数を取得する。"""

    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"環境変数 {name} が設定されていません。"
        )

    return value.strip()


def create_client() -> tuple[OpenAI, str, str]:
    """Azure OpenAIクライアントを作成する。"""

    load_dotenv(
        dotenv_path=ENV_FILE,
        encoding="utf-8-sig",
        override=True,
    )

    endpoint = get_required_environment_variable(
        "AZURE_OPENAI_ENDPOINT"
    )
    api_key = get_required_environment_variable(
        "AZURE_OPENAI_API_KEY"
    )
    chat_deployment = get_required_environment_variable(
        "AZURE_OPENAI_CHAT_DEPLOYMENT"
    )
    embedding_deployment = (
        get_required_environment_variable(
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
        )
    )

    base_url = f"{endpoint.rstrip('/')}/openai/v1/"

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=30.0,
        max_retries=2,
    )

    return client, chat_deployment, embedding_deployment


def check_chat(
    client: OpenAI,
    deployment_name: str,
) -> None:
    """Chatモデルとの疎通を確認する。"""

    print("=== Azure OpenAI Chat疎通確認 ===")
    print("使用するChatデプロイ名:", repr(deployment_name))

    response = client.responses.create(
        model=deployment_name,
        instructions=(
            "あなたは接続確認用のアシスタントです。"
            "回答は短くしてください。"
        ),
        input=(
            "Azure OpenAIとの疎通確認です。"
            "「接続成功」と回答してください。"
        ),
        max_output_tokens=100,
    )

    answer = response.output_text.strip()

    if not answer:
        raise RuntimeError(
            "Chatモデルから空の応答が返されました。"
        )

    print("Chat接続: 成功")
    print("Chat応答:", answer)


def check_embedding(
    client: OpenAI,
    deployment_name: str,
) -> None:
    """Embeddingモデルとの疎通を確認する。"""

    print()
    print("=== Azure OpenAI Embedding疎通確認 ===")
    print(
        "使用するEmbeddingデプロイ名:",
        repr(deployment_name),
    )

    response = client.embeddings.create(
        model=deployment_name,
        input="設備Aで振動異常を検出しました。",
    )

    if not response.data:
        raise RuntimeError(
            "Embeddingデータが返されませんでした。"
        )

    embedding = response.data[0].embedding

    if not embedding:
        raise RuntimeError(
            "Embeddingベクトルが空です。"
        )

    dimensions = len(embedding)

    print("Embedding接続: 成功")
    print("Embedding次元数:", dimensions)
    print("先頭5要素:", embedding[:5])

    if dimensions != EXPECTED_EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            "Embedding次元数がDB定義と一致しません。"
            f" expected={EXPECTED_EMBEDDING_DIMENSIONS}"
            f" actual={dimensions}"
        )

    print("DB定義 vector(1536)との一致確認: 成功")


def main() -> None:
    """ChatとEmbeddingの疎通を確認する。"""

    client, chat_deployment, embedding_deployment = (
        create_client()
    )

    check_chat(
        client=client,
        deployment_name=chat_deployment,
    )

    check_embedding(
        client=client,
        deployment_name=embedding_deployment,
    )


if __name__ == "__main__":
    try:
        main()

    except AuthenticationError:
        print(
            "認証エラー: APIキーを確認してください。"
        )
        raise SystemExit(1)

    except RateLimitError:
        print(
            "レート制限エラー: Azure OpenAIの"
            "クォータを確認してください。"
        )
        raise SystemExit(1)

    except APIConnectionError as exc:
        print(
            "接続エラー: Azure OpenAIへ接続できませんでした。"
        )
        print("エラー内容:", str(exc))
        raise SystemExit(1) from exc

    except APIStatusError as exc:
        print(
            f"Azure OpenAI APIエラー: HTTP {exc.status_code}"
        )
        print("エラー内容:", str(exc))

        response = exc.response

        print("リクエストURL:", response.request.url)
        print("Azure応答本文:", response.text)

        try:
            print(
                "AzureエラーJSON:",
                response.json(),
            )
        except Exception:
            print(
                "Azure応答をJSONとして解析できませんでした。"
            )

        raise SystemExit(1) from exc
