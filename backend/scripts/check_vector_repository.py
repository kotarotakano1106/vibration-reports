import os
from pathlib import Path

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    OpenAI,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from backend.src.db.session import SessionLocal
from backend.src.models.report import Report
from backend.src.repositories.vector_repository import (
    VectorRepository,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

EMBEDDING_DIMENSIONS = 1536
TEST_EQUIPMENT_ID = "MOTOR-001"


def get_required_value(name):
    """必須環境変数を取得する。"""

    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"環境変数 {name} が設定されていません。"
        )

    return value.strip()


def create_embedding_client():
    """Embedding用Azure OpenAIクライアントを作成する。"""

    endpoint = get_required_value(
        "AZURE_OPENAI_EMBEDDING_ENDPOINT"
    )

    api_key = get_required_value(
        "AZURE_OPENAI_EMBEDDING_API_KEY"
    )

    base_url = f"{endpoint.rstrip('/')}/openai/v1/"

    return OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=30.0,
        max_retries=2,
    )


def create_embedding(
    client,
    deployment_name,
    text,
):
    """文章からEmbeddingを生成する。"""

    response = client.embeddings.create(
        model=deployment_name,
        input=text,
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

    if dimensions != EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            "Embedding次元数がDB定義と一致しません。"
            f" expected={EMBEDDING_DIMENSIONS}"
            f" actual={dimensions}"
        )

    return embedding


def get_latest_report(session):
    """MOTOR-001の最新レポートを取得する。"""

    statement = (
        select(Report)
        .where(
            Report.equipment_id == TEST_EQUIPMENT_ID
        )
        .order_by(
            Report.created_at.desc()
        )
        .limit(1)
    )

    return session.scalar(statement)


def build_report_content(report):
    """レポートからRAG検索対象テキストを作成する。"""

    parts = [
        f"対象設備: {report.equipment_id}",
        f"測定日: {report.measurement_date}",
        f"タイトル: {report.title}",
        f"測定件数: {report.record_count}",
        f"最小振動値: {report.minimum_value}",
        f"最大振動値: {report.maximum_value}",
        f"平均振動値: {report.average_value}",
        f"異常検知件数: {report.anomaly_count}",
        f"判定: {report.status}",
        f"分析概要: {report.ai_summary}",
        f"分析結果: {report.ai_analysis}",
        f"推奨対応: {report.recommendation or 'なし'}",
        f"レポート本文: {report.report_text}",
    ]

    return "\n".join(parts)


def show_search_result(result, rank):
    """類似検索結果を表示する。"""

    report_chunk = result["report_chunk"]
    distance = result["distance"]

    print()
    print("検索順位:", rank)
    print("チャンクID:", report_chunk.id)
    print("レポートID:", report_chunk.report_id)
    print("設備ID:", report_chunk.equipment_id)
    print("測定日:", report_chunk.measurement_date)
    print("チャンク番号:", report_chunk.chunk_index)
    print("チャンク種別:", report_chunk.chunk_type)
    print("Embeddingモデル:", report_chunk.embedding_model)
    print("コサイン距離:", distance)
    print("内容先頭:", report_chunk.content[:100])


def main():
    """Embeddingの保存とpgvector類似検索を確認する。"""

    load_dotenv(
        dotenv_path=ENV_FILE,
        encoding="utf-8-sig",
        override=True,
    )

    deployment_name = get_required_value(
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
    )

    embedding_client = create_embedding_client()

    print("=== VectorRepository確認 ===")
    print(
        "Embeddingデプロイ名:",
        repr(deployment_name),
    )
    print(
        "期待するEmbedding次元数:",
        EMBEDDING_DIMENSIONS,
    )

    with SessionLocal() as session:
        repository = VectorRepository(session)

        report = get_latest_report(session)

        if report is None:
            raise RuntimeError(
                "MOTOR-001のレポートが存在しません。"
                "ReportRepositoryの確認を先に"
                "実行してください。"
            )

        print("対象レポートID:", report.id)
        print("対象レポート:", report.title)

        existing_chunk = (
            repository.get_by_report_and_index(
                report.id,
                0,
            )
        )

        if existing_chunk is None:
            report_content = build_report_content(
                report
            )

            print()
            print(
                "レポートEmbeddingを生成しています。"
            )

            report_embedding = create_embedding(
                embedding_client,
                deployment_name,
                report_content,
            )

            print(
                "レポートEmbedding次元数:",
                len(report_embedding),
            )

            try:
                created_chunk = repository.create(
                    report_id=report.id,
                    chunk_index=0,
                    chunk_type="full_report",
                    content=report_content,
                    embedding=report_embedding,
                    embedding_model=deployment_name,
                    embedding_version="1",
                    equipment_id=report.equipment_id,
                    measurement_date=(
                        report.measurement_date
                    ),
                    metadata_json={
                        "status": report.status,
                        "anomaly_count": (
                            report.anomaly_count
                        ),
                        "maximum_value": (
                            report.maximum_value
                        ),
                    },
                )

                session.commit()
                session.refresh(created_chunk)

            except IntegrityError as exc:
                session.rollback()

                raise RuntimeError(
                    "report_chunksへの登録に"
                    "失敗しました。"
                    "外部キー、一意制約、"
                    "Embedding次元数を確認してください。"
                ) from exc

            print("report_chunks登録: 成功")
            print("チャンクID:", created_chunk.id)

        else:
            print()
            print(
                "登録済みレポートチャンクを"
                "取得しました。"
            )
            print("チャンクID:", existing_chunk.id)

        question = (
            "MOTOR-001で振動値が閾値を超えた"
            "レポートと推奨対応を教えてください。"
        )

        print()
        print("検索質問:", question)
        print("質問Embeddingを生成しています。")

        query_embedding = create_embedding(
            embedding_client,
            deployment_name,
            question,
        )

        print(
            "質問Embedding次元数:",
            len(query_embedding),
        )

        results = repository.search_similar(
            query_embedding=query_embedding,
            equipment_id=TEST_EQUIPMENT_ID,
            limit=5,
        )

        if not results:
            raise RuntimeError(
                "類似検索結果がありませんでした。"
            )

        print()
        print("pgvector類似検索: 成功")
        print("検索結果件数:", len(results))

        for rank, result in enumerate(
            results,
            start=1,
        ):
            show_search_result(
                result,
                rank,
            )


if __name__ == "__main__":
    try:
        main()

    except AuthenticationError:
        print(
            "認証エラー: Embedding用APIキーを"
            "確認してください。"
        )
        raise SystemExit(1)

    except APIConnectionError as exc:
        print(
            "接続エラー: Azure OpenAIへ"
            "接続できませんでした。"
        )
        print("エラー内容:", str(exc))
        raise SystemExit(1) from exc

    except APIStatusError as exc:
        print(
            "Azure OpenAI APIエラー:",
            exc.status_code,
        )
        print("エラー内容:", str(exc))
        print(
            "リクエストURL:",
            exc.response.request.url,
        )
        raise SystemExit(1) from exc

    except Exception as exc:
        print(
            "VectorRepository確認失敗:",
            type(exc).__name__,
            str(exc),
        )
        raise SystemExit(1) from exc
        