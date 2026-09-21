import pandas as pd

from backend.src.services.vibration_analysis_service import (
    VibrationAnalysisService,
    VibrationAnalysisServiceError,
    VibrationDataEmptyError,
    VibrationThresholdError,
)


def create_test_dataframe():
    """確認用の振動DataFrameを作成する。"""

    return pd.DataFrame(
        {
            "measured_at": pd.to_datetime(
                [
                    "2026-09-01T09:00:00+09:00",
                    "2026-09-01T09:00:10+09:00",
                    "2026-09-01T09:00:20+09:00",
                ],
                utc=True,
            ),
            "vibration_value": [
                0.4,
                0.6,
                2.5,
            ],
        }
    )


def show_result(result):
    """分析結果を表示する。"""

    print("測定件数:", result.record_count)
    print("最小値:", result.minimum_value)
    print("最大値:", result.maximum_value)
    print("平均値:", result.average_value)
    print("中央値:", result.median_value)
    print(
        "標準偏差:",
        result.standard_deviation,
    )
    print("閾値:", result.threshold_value)
    print("異常件数:", result.anomaly_count)
    print("異常率:", result.anomaly_rate)
    print("判定:", result.status)

    for anomaly in result.anomalies:
        print()
        print(
            "異常行番号:",
            anomaly.row_number,
        )
        print(
            "異常測定日時:",
            anomaly.measured_at,
        )
        print(
            "異常振動値:",
            anomaly.value,
        )
        print(
            "閾値超過量:",
            anomaly.excess_value,
        )


def check_anomaly_result(service):
    """閾値超過ありの分析結果を確認する。"""

    dataframe = create_test_dataframe()

    result = service.analyze(
        dataframe,
        threshold_value=2.0,
    )

    print("=== 閾値超過あり ===")
    show_result(result)

    if result.record_count != 3:
        raise RuntimeError(
            "測定件数が期待値と一致しません。"
        )

    if result.minimum_value != 0.4:
        raise RuntimeError(
            "最小値が期待値と一致しません。"
        )

    if result.maximum_value != 2.5:
        raise RuntimeError(
            "最大値が期待値と一致しません。"
        )

    if result.median_value != 0.6:
        raise RuntimeError(
            "中央値が期待値と一致しません。"
        )

    if result.anomaly_count != 1:
        raise RuntimeError(
            "異常件数が期待値と一致しません。"
        )

    if result.status != "requires_attention":
        raise RuntimeError(
            "判定が期待値と一致しません。"
        )

    print()
    print("閾値超過ありの分析: 成功")


def check_normal_result(service):
    """閾値超過なしの分析結果を確認する。"""

    dataframe = create_test_dataframe()

    result = service.analyze(
        dataframe,
        threshold_value=3.0,
    )

    print()
    print("=== 閾値超過なし ===")
    print("異常件数:", result.anomaly_count)
    print("判定:", result.status)

    if result.anomaly_count != 0:
        raise RuntimeError(
            "正常データで異常が検出されました。"
        )

    if result.status != "normal":
        raise RuntimeError(
            "正常判定になりませんでした。"
        )

    print("閾値超過なしの分析: 成功")


def check_invalid_threshold(service):
    """不正な閾値を検出できるか確認する。"""

    dataframe = create_test_dataframe()

    try:
        service.analyze(
            dataframe,
            threshold_value=0,
        )

    except VibrationThresholdError as exc:
        print()
        print("不正閾値の検出: 成功")
        print("エラー内容:", str(exc))
        return

    raise RuntimeError(
        "不正な閾値を検出できませんでした。"
    )


def check_empty_dataframe(service):
    """空データを検出できるか確認する。"""

    dataframe = pd.DataFrame(
        columns=[
            "measured_at",
            "vibration_value",
        ]
    )

    try:
        service.analyze(
            dataframe,
            threshold_value=2.0,
        )

    except VibrationDataEmptyError as exc:
        print()
        print("空データの検出: 成功")
        print("エラー内容:", str(exc))
        return

    raise RuntimeError(
        "空データを検出できませんでした。"
    )


def main():
    """VibrationAnalysisServiceを確認する。"""

    service = VibrationAnalysisService()

    print(
        "=== VibrationAnalysisService確認 ==="
    )

    check_anomaly_result(service)
    check_normal_result(service)
    check_invalid_threshold(service)
    check_empty_dataframe(service)

    print()
    print(
        "VibrationAnalysisServiceの"
        "全確認: 成功"
    )


if __name__ == "__main__":
    try:
        main()

    except VibrationAnalysisServiceError as exc:
        print(
            "VibrationAnalysisService確認失敗:",
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