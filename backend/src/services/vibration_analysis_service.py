from dataclasses import asdict, dataclass

import pandas as pd


class VibrationAnalysisServiceError(Exception):
    """振動分析Serviceの共通エラー。"""


class VibrationDataEmptyError(
    VibrationAnalysisServiceError
):
    """分析対象データが空の場合のエラー。"""


class VibrationColumnError(
    VibrationAnalysisServiceError
):
    """分析に必要な列が存在しない場合のエラー。"""


class VibrationThresholdError(
    VibrationAnalysisServiceError
):
    """閾値が不正な場合のエラー。"""


class VibrationValueError(
    VibrationAnalysisServiceError
):
    """振動値が不正な場合のエラー。"""


@dataclass(frozen=True)
class VibrationAnomaly:
    """閾値を超過した振動データ。"""

    row_number: int
    measured_at: str
    value: float
    threshold: float
    excess_value: float

    def to_dict(self):
        """辞書へ変換する。"""

        return asdict(self)


@dataclass(frozen=True)
class VibrationAnalysisResult:
    """振動分析結果。"""

    record_count: int
    minimum_value: float
    maximum_value: float
    average_value: float
    median_value: float
    standard_deviation: float
    threshold_value: float
    anomaly_count: int
    anomaly_rate: float
    status: str
    anomalies: tuple

    def to_dict(self):
        """辞書へ変換する。"""

        result = asdict(self)

        result["anomalies"] = [
            anomaly.to_dict()
            for anomaly in self.anomalies
        ]

        return result


class VibrationAnalysisService:
    """振動値の統計計算と閾値判定を担当するService。"""

    DATETIME_COLUMN = "measured_at"
    VALUE_COLUMN = "vibration_value"

    STATUS_NORMAL = "normal"
    STATUS_REQUIRES_ATTENTION = "requires_attention"

    def analyze(
        self,
        dataframe,
        *,
        threshold_value,
    ):
        """DataFrameを分析して統計結果を返す。"""

        self._validate_dataframe(dataframe)
        self._validate_threshold(threshold_value)

        values = dataframe[
            self.VALUE_COLUMN
        ].astype(float)

        record_count = len(values)

        minimum_value = float(values.min())
        maximum_value = float(values.max())
        average_value = float(values.mean())
        median_value = float(values.median())

        standard_deviation = float(
            values.std(ddof=0)
        )

        anomalies = self._find_anomalies(
            dataframe=dataframe,
            threshold_value=float(
                threshold_value
            ),
        )

        anomaly_count = len(anomalies)

        anomaly_rate = (
            anomaly_count / record_count
        )

        status = self._determine_status(
            anomaly_count=anomaly_count
        )

        return VibrationAnalysisResult(
            record_count=record_count,
            minimum_value=minimum_value,
            maximum_value=maximum_value,
            average_value=average_value,
            median_value=median_value,
            standard_deviation=standard_deviation,
            threshold_value=float(
                threshold_value
            ),
            anomaly_count=anomaly_count,
            anomaly_rate=float(anomaly_rate),
            status=status,
            anomalies=tuple(anomalies),
        )

    def _validate_dataframe(
        self,
        dataframe,
    ):
        """分析対象DataFrameを検証する。"""

        if not isinstance(
            dataframe,
            pd.DataFrame,
        ):
            raise VibrationAnalysisServiceError(
                "分析対象はDataFrameで"
                "ある必要があります。"
            )

        if dataframe.empty:
            raise VibrationDataEmptyError(
                "分析対象データが空です。"
            )

        required_columns = {
            self.DATETIME_COLUMN,
            self.VALUE_COLUMN,
        }

        missing_columns = (
            required_columns
            - set(dataframe.columns)
        )

        if missing_columns:
            missing_text = ", ".join(
                sorted(missing_columns)
            )

            raise VibrationColumnError(
                "分析に必要な列が不足しています。"
                f" missing={missing_text}"
            )

        if dataframe[
            self.VALUE_COLUMN
        ].isna().any():
            raise VibrationValueError(
                "振動値に欠損値があります。"
            )

        if not pd.api.types.is_numeric_dtype(
            dataframe[self.VALUE_COLUMN]
        ):
            raise VibrationValueError(
                "振動値が数値型ではありません。"
            )

    def _validate_threshold(
        self,
        threshold_value,
    ):
        """閾値を検証する。"""

        if isinstance(threshold_value, bool):
            raise VibrationThresholdError(
                "閾値は数値で指定してください。"
            )

        try:
            converted_threshold = float(
                threshold_value
            )

        except (TypeError, ValueError) as exc:
            raise VibrationThresholdError(
                "閾値を数値へ変換できません。"
            ) from exc

        if converted_threshold <= 0:
            raise VibrationThresholdError(
                "閾値は0より大きい値を"
                "指定してください。"
            )

    def _find_anomalies(
        self,
        *,
        dataframe,
        threshold_value,
    ):
        """閾値を超過した測定値を抽出する。"""

        anomaly_dataframe = dataframe[
            dataframe[self.VALUE_COLUMN]
            > threshold_value
        ]

        anomalies = []

        for index, row in (
            anomaly_dataframe.iterrows()
        ):
            measured_at = row[
                self.DATETIME_COLUMN
            ]

            if hasattr(
                measured_at,
                "isoformat",
            ):
                measured_at_text = (
                    measured_at.isoformat()
                )
            else:
                measured_at_text = str(
                    measured_at
                )

            value = float(
                row[self.VALUE_COLUMN]
            )

            anomaly = VibrationAnomaly(
                row_number=int(index) + 2,
                measured_at=measured_at_text,
                value=value,
                threshold=threshold_value,
                excess_value=(
                    value - threshold_value
                ),
            )

            anomalies.append(anomaly)

        return anomalies

    def _determine_status(
        self,
        *,
        anomaly_count,
    ):
        """異常件数から判定ステータスを決定する。"""

        if anomaly_count > 0:
            return self.STATUS_REQUIRES_ATTENTION

        return self.STATUS_NORMAL
        
