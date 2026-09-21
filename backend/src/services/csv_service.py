from pathlib import Path
from typing import ClassVar

import pandas as pd


class CsvServiceError(Exception):
    """CsvServiceの共通エラー。"""


class CsvFileNotFoundError(CsvServiceError):
    """CSVファイルが存在しない場合のエラー。"""


class CsvReadError(CsvServiceError):
    """CSVファイルを読み込めない場合のエラー。"""


class CsvEmptyError(CsvServiceError):
    """CSVにデータ行が存在しない場合のエラー。"""


class CsvRequiredColumnError(CsvServiceError):
    """CSVの必須列が不足している場合のエラー。"""


class CsvInvalidDatetimeError(CsvServiceError):
    """日時列を変換できない場合のエラー。"""


class CsvInvalidValueError(CsvServiceError):
    """振動値を数値へ変換できない場合のエラー。"""


class CsvMissingValueError(CsvServiceError):
    """必須項目に欠損値がある場合のエラー。"""


class CsvService:
    """振動測定CSVの読込と検証を担当するService。"""

    DATETIME_COLUMN = "measured_at"
    VALUE_COLUMN = "vibration_value"

    REQUIRED_COLUMNS: ClassVar[set[str]] = {
        DATETIME_COLUMN,
        VALUE_COLUMN,
    }

    def load(self, file_path, encoding="utf-8"):
        """CSVを読み込み、分析可能なDataFrameを返す。"""

        path = Path(file_path)

        if not path.exists():
            raise CsvFileNotFoundError(
                f"CSVファイルが存在しません: {path}"
            )

        if not path.is_file():
            raise CsvFileNotFoundError(
                f"指定されたパスはファイルではありません: {path}"
            )

        try:
            dataframe = pd.read_csv(
                path,
                encoding=encoding,
                on_bad_lines="error",
            )

        except UnicodeDecodeError as exc:
            raise CsvReadError(
                "CSVの文字コードが正しくありません。"
                f" encoding={encoding}"
            ) from exc

        except pd.errors.EmptyDataError as exc:
            raise CsvEmptyError(
                "CSVファイルが空です。"
            ) from exc

        except pd.errors.ParserError as exc:
            raise CsvReadError(
                "CSVの形式が正しくありません。"
            ) from exc

        except OSError as exc:
            raise CsvReadError(
                "CSVファイルを読み込めませんでした。"
            ) from exc

        return self.validate(dataframe)

    def validate(self, dataframe):
        """DataFrameの必須列とデータ内容を検証する。"""

        if dataframe.empty:
            raise CsvEmptyError(
                "CSVにデータ行がありません。"
            )

        normalized_dataframe = dataframe.copy()

        normalized_dataframe.columns = [
            str(column).strip()
            for column in normalized_dataframe.columns
        ]

        missing_columns = (
            self.REQUIRED_COLUMNS
            - set(normalized_dataframe.columns)
        )

        if missing_columns:
            missing_column_text = ", ".join(
                sorted(missing_columns)
            )

            raise CsvRequiredColumnError(
                "CSVの必須列が不足しています。"
                f" missing={missing_column_text}"
            )

        required_dataframe = (
            normalized_dataframe[
                [
                    self.DATETIME_COLUMN,
                    self.VALUE_COLUMN,
                ]
            ]
            .copy()
        )

        self._validate_missing_values(
            required_dataframe
        )

        required_dataframe[
            self.DATETIME_COLUMN
        ] = self._convert_datetime_column(
            required_dataframe[
                self.DATETIME_COLUMN
            ]
        )

        required_dataframe[
            self.VALUE_COLUMN
        ] = self._convert_value_column(
            required_dataframe[
                self.VALUE_COLUMN
            ]
        )

        self._validate_missing_values(
            required_dataframe
        )

        required_dataframe = (
            required_dataframe
            .sort_values(
                by=self.DATETIME_COLUMN,
                ascending=True,
            )
            .reset_index(drop=True)
        )

        return required_dataframe

    def _validate_missing_values(
        self,
        dataframe,
    ):
        """必須列の欠損値を確認する。"""

        missing_counts = (
            dataframe[
                [
                    self.DATETIME_COLUMN,
                    self.VALUE_COLUMN,
                ]
            ]
            .isna()
            .sum()
        )

        missing_messages = []

        for column_name, count in missing_counts.items():
            if int(count) > 0:
                missing_messages.append(
                    f"{column_name}={int(count)}件"
                )

        if missing_messages:
            raise CsvMissingValueError(
                "CSVの必須項目に欠損値があります。"
                + " "
                + ", ".join(missing_messages)
            )

        datetime_empty = (
            dataframe[self.DATETIME_COLUMN]
            .astype(str)
            .str.strip()
            .eq("")
        )

        value_empty = (
            dataframe[self.VALUE_COLUMN]
            .astype(str)
            .str.strip()
            .eq("")
        )

        if datetime_empty.any() or value_empty.any():
            details = []

            if datetime_empty.any():
                details.append(
                    "measured_at="
                    f"{int(datetime_empty.sum())}件"
                )

            if value_empty.any():
                details.append(
                    "vibration_value="
                    f"{int(value_empty.sum())}件"
                )

            raise CsvMissingValueError(
                "CSVの必須項目に空文字があります。"
                + " "
                + ", ".join(details)
            )

    def _convert_datetime_column(
        self,
        datetime_series,
    ):
        """日時列を日時型へ変換する。"""

        converted_series = pd.to_datetime(
            datetime_series,
            errors="coerce",
            utc=True,
        )

        invalid_rows = converted_series.isna()

        if invalid_rows.any():
            row_numbers = [
                int(index) + 2
                for index in converted_series[
                    invalid_rows
                ].index.tolist()
            ]

            raise CsvInvalidDatetimeError(
                "measured_atを日時へ変換できません。"
                f" rows={row_numbers}"
            )

        return converted_series

    def _convert_value_column(
        self,
        value_series,
    ):
        """振動値列を数値型へ変換する。"""

        converted_series = pd.to_numeric(
            value_series,
            errors="coerce",
        )

        invalid_rows = converted_series.isna()

        if invalid_rows.any():
            row_numbers = [
                int(index) + 2
                for index in converted_series[
                    invalid_rows
                ].index.tolist()
            ]

            raise CsvInvalidValueError(
                "vibration_valueを数値へ"
                "変換できません。"
                f" rows={row_numbers}"
            )

        return converted_series.astype(float)