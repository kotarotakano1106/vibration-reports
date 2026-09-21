from math import sqrt

import pandas as pd
import pytest

from backend.src.services.vibration_analysis_service import (
    VibrationAnalysisService,
    VibrationAnalysisServiceError,
    VibrationColumnError,
    VibrationDataEmptyError,
    VibrationThresholdError,
    VibrationValueError,
)


def create_dataframe(
    values: list[float],
) -> pd.DataFrame:
    """テスト用の振動データを作成する。"""

    return pd.DataFrame(
        {
            "measured_at": pd.date_range(
                start="2026-09-01T10:00:00+09:00",
                periods=len(values),
                freq="s",
            ),
            "vibration_value": values,
        }
    )


def test_analyze_returns_statistics_and_normal_status() -> None:
    """閾値超過がなければ統計値と正常Statusを返す。"""

    dataframe = create_dataframe(
        [1.0, 2.0, 3.0],
    )

    result = VibrationAnalysisService().analyze(
        dataframe,
        threshold_value=3.0,
    )

    assert result.record_count == 3
    assert result.minimum_value == pytest.approx(1.0)
    assert result.maximum_value == pytest.approx(3.0)
    assert result.average_value == pytest.approx(2.0)
    assert result.median_value == pytest.approx(2.0)
    assert result.standard_deviation == pytest.approx(
        sqrt(2 / 3),
    )
    assert result.threshold_value == pytest.approx(3.0)
    assert result.anomaly_count == 0
    assert result.anomaly_rate == pytest.approx(0.0)
    assert result.status == "normal"
    assert result.anomalies == ()


def test_analyze_detects_values_above_threshold() -> None:
    """閾値を超えた値を異常として抽出する。"""

    dataframe = create_dataframe(
        [1.0, 2.5, 4.0],
    )

    result = VibrationAnalysisService().analyze(
        dataframe,
        threshold_value=2.0,
    )

    assert result.anomaly_count == 2
    assert result.anomaly_rate == pytest.approx(2 / 3)
    assert result.status == "requires_attention"

    first_anomaly = result.anomalies[0]

    assert first_anomaly.row_number == 3
    assert first_anomaly.value == pytest.approx(2.5)
    assert first_anomaly.threshold == pytest.approx(2.0)
    assert first_anomaly.excess_value == pytest.approx(0.5)

    second_anomaly = result.anomalies[1]

    assert second_anomaly.row_number == 4
    assert second_anomaly.value == pytest.approx(4.0)
    assert second_anomaly.excess_value == pytest.approx(2.0)


def test_value_equal_to_threshold_is_not_anomaly() -> None:
    """閾値と等しい値は異常として扱わない。"""

    dataframe = create_dataframe(
        [1.0, 2.0],
    )

    result = VibrationAnalysisService().analyze(
        dataframe,
        threshold_value=2.0,
    )

    assert result.anomaly_count == 0
    assert result.status == "normal"


def test_result_can_be_converted_to_dictionary() -> None:
    """分析結果と異常詳細を辞書へ変換できる。"""

    dataframe = create_dataframe(
        [1.0, 3.0],
    )

    result = VibrationAnalysisService().analyze(
        dataframe,
        threshold_value=2.0,
    )

    result_dict = result.to_dict()

    assert result_dict["record_count"] == 2
    assert result_dict["status"] == "requires_attention"
    assert len(result_dict["anomalies"]) == 1
    assert result_dict["anomalies"][0]["value"] == pytest.approx(
        3.0
    )


def test_analyze_raises_when_dataframe_is_empty() -> None:
    """空のDataFrameでは専用例外を送出する。"""

    dataframe = pd.DataFrame(
        columns=[
            "measured_at",
            "vibration_value",
        ]
    )

    with pytest.raises(VibrationDataEmptyError):
        VibrationAnalysisService().analyze(
            dataframe,
            threshold_value=2.0,
        )


def test_analyze_raises_when_input_is_not_dataframe() -> None:
    """DataFrame以外の入力では共通例外を送出する。"""

    with pytest.raises(VibrationAnalysisServiceError):
        VibrationAnalysisService().analyze(
            [],
            threshold_value=2.0,
        )


@pytest.mark.parametrize(
    "missing_column",
    [
        "measured_at",
        "vibration_value",
    ],
)
def test_analyze_raises_when_required_column_is_missing(
    missing_column: str,
) -> None:
    """必須列が不足している場合は専用例外を送出する。"""

    dataframe = create_dataframe(
        [1.0],
    ).drop(columns=[missing_column])

    with pytest.raises(VibrationColumnError):
        VibrationAnalysisService().analyze(
            dataframe,
            threshold_value=2.0,
        )


def test_analyze_raises_when_vibration_value_is_missing() -> None:
    """振動値に欠損値がある場合は専用例外を送出する。"""

    dataframe = create_dataframe(
        [1.0, 2.0],
    )
    dataframe.loc[1, "vibration_value"] = None

    with pytest.raises(VibrationValueError):
        VibrationAnalysisService().analyze(
            dataframe,
            threshold_value=2.0,
        )


def test_analyze_raises_when_vibration_value_is_not_numeric() -> None:
    """振動値が数値型でない場合は専用例外を送出する。"""

    dataframe = pd.DataFrame(
        {
            "measured_at": [
                "2026-09-01T10:00:00+09:00",
            ],
            "vibration_value": [
                "invalid",
            ],
        }
    )

    with pytest.raises(VibrationValueError):
        VibrationAnalysisService().analyze(
            dataframe,
            threshold_value=2.0,
        )


@pytest.mark.parametrize(
    "threshold_value",
    [
        0,
        -1,
        "invalid",
        None,
        True,
    ],
)
def test_analyze_raises_when_threshold_is_invalid(
    threshold_value: object,
) -> None:
    """不正な閾値では専用例外を送出する。"""

    dataframe = create_dataframe(
        [1.0],
    )

    with pytest.raises(VibrationThresholdError):
        VibrationAnalysisService().analyze(
            dataframe,
            threshold_value=threshold_value,
        )


def test_analyze_accepts_numeric_string_threshold() -> None:
    """数値文字列の閾値を受け付ける。"""

    dataframe = create_dataframe(
        [1.0, 3.0],
    )

    result = VibrationAnalysisService().analyze(
        dataframe,
        threshold_value="2.0",
    )

    assert result.threshold_value == pytest.approx(2.0)
    assert result.anomaly_count == 1
