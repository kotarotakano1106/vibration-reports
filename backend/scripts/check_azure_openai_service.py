from backend.src.services.azure_openai_service import (
    AzureOpenAIService,
    AzureOpenAIServiceError,
)


def main():
    """AzureOpenAIServiceの基本動作を確認する。"""

    service = AzureOpenAIService()

    print("=== AzureOpenAIService確認 ===")
    print(
        "Chatデプロイ名:",
        repr(service.chat_deployment),
    )
    print(
        "Embeddingデプロイ名:",
        repr(service.embedding_deployment),
    )

    print()
    print("振動AI分析を生成しています。")

    analysis = service.generate_vibration_analysis(
        equipment_id="MOTOR-001",
        measurement_date="2026-09-01",
        record_count=3,
        minimum_value=0.4,
        maximum_value=2.5,
        average_value=1.1667,
        median_value=0.6,
        standard_deviation=0.9437,
        threshold_value=2.0,
        anomaly_count=1,
    )

    print("Chat文章生成: 成功")
    print()
    print(analysis)

    print()
    print("Embeddingを生成しています。")

    embedding = service.create_embedding(
        (
            "MOTOR-001の振動測定では、"
            "最大値2.5を記録しました。"
            "閾値2.0を超える測定値を"
            "1件検出しました。"
        )
    )

    print("Embedding生成: 成功")
    print("Embedding次元数:", len(embedding))
    print("先頭5要素:", embedding[:5])


if __name__ == "__main__":
    try:
        main()

    except AzureOpenAIServiceError as exc:
        print(
            "AzureOpenAIService確認失敗:",
            type(exc).__name__,
            str(exc),
        )
        raise SystemExit(1) from exc

    except Exception as exc:
        print(
            "予期しないエラー:",
            type(exc).__name__,
            str(exc),
        )
        raise SystemExit(1) from exc
