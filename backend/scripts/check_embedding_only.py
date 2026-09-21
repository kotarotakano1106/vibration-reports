import os
from pathlib import Path

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    OpenAI,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

EXPECTED_DIMENSIONS = 1536


def get_required_value(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"環境変数 {name} が設定されていません。"
        )

    return value.strip()


def main() -> None:
    load_dotenv(
        dotenv_path=ENV_FILE,
        encoding="utf-8-sig",
        override=True,
    )

    endpoint = get_required_value(
        "AZURE_OPENAI_EMBEDDING_ENDPOINT"
    )
    api_key = get_required_value(
        "AZURE_OPENAI_EMBEDDING_API_KEY"
    )
    deployment = get_required_value(
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
    )

    base_url = f"{endpoint.rstrip('/')}/openai/v1/"

    print("=== Azure OpenAI Embedding単体疎通確認 ===")
    print("Embeddingデプロイ名:", repr(deployment))
    print("Embedding送信先:", f"{base_url}embeddings")

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=30.0,
        max_retries=2,
    )

    response = client.embeddings.create(
        model=deployment,
        input="設備Aで振動異常を検出しました。",
    )

    if not response.data:
        raise RuntimeError(
            "Embeddingデータが返されませんでした。"
        )

    embedding = response.data[0].embedding
    dimensions = len(embedding)

    print("Embedding接続: 成功")
    print("Embedding次元数:", dimensions)
    print("先頭5要素:", embedding[:5])

    if dimensions != EXPECTED_DIMENSIONS:
        raise RuntimeError(
            "DBのベクトル次元数と一致しません。"
            f" expected={EXPECTED_DIMENSIONS}"
            f" actual={dimensions}"
        )

    print("DB定義 vector(1536)との一致確認: 成功")


if __name__ == "__main__":
    try:
        main()

    except AuthenticationError:
        print(
            "認証エラー: Azure OpenAIリソースの"
            "APIキーを確認してください。"
        )
        raise SystemExit(1)

    except APIConnectionError as exc:
        print(
            "接続エラー: Azure OpenAIへ接続できません。"
        )
        print("エラー内容:", str(exc))
        raise SystemExit(1) from exc

    except APIStatusError as exc:
        print(
            f"Azure OpenAI APIエラー: HTTP {exc.status_code}"
        )
        print("エラー内容:", str(exc))
        print("リクエストURL:", exc.response.request.url)
        print("Azure応答本文:", exc.response.text)
        raise SystemExit(1) from exc

    except Exception as exc:
        print(
            "Embedding疎通確認失敗:",
            type(exc).__name__,
            str(exc),
        )
        raise SystemExit(1) from exc
