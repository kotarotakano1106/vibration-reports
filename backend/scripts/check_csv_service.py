from pathlib import Path
from tempfile import TemporaryDirectory

from backend.src.services.csv_service import (
    CsvInvalidDatetimeError,
    CsvInvalidValueError,
    CsvMissingValueError,
    CsvRequiredColumnError,
    CsvService,
    CsvServiceError,
)


VALID_CSV = (
    "measured_at,vibration_value\n"
    "2026-09-01T09:00:20+09:00,2.50\n"
    "2026-09-01T09:00:00+09:00,0.40\n"
    "2026-09-01T09:00:10+09:00,0.60\n"
)

MISSING_COLUMN_CSV = (
    "measured_at,value\n"
    "2026-09-01T09:00:00+09:00,0.40\n"
)

INVALID_DATETIME_CSV = (
    "measured_at,vibration_value\n"
    "invalid-datetime,0.40\n"
)

INVALID_VALUE_CSV = (
    "measured_at,vibration_value\n"
    "2026-09-01T09:00:00+09:00,not-number\n"
)

MISSING_VALUE_CSV = (
    "measured_at,vibration_value\n"
    "2026-09-01T09:00:00+09:00,\n"
)


def write_test_file(
    directory,
    filename,
    content,
):
    """一時ディレクトリへ確認用CSVを保存する。"""

    path = Path(directory) / filename

    path.write_text(
        content,
        encoding="utf-8",
    )

    return path


def check_valid_csv(
    service,
    directory,
):
    """正常CSVの読込を確認する。"""

    path = write_test_file(
        directory,
        "valid.csv",
        VALID_CSV,
    )

    dataframe = service.load(path)

    print("正常CSV読込: 成功")
    print("行数:", len(dataframe))
    print(
        "列名:",
        list(dataframe.columns),
    )
    print(
        "日時データ型:",
        dataframe["measured_at"].dtype,
    )
    print(
        "振動値データ型:",
        dataframe["vibration_value"].dtype,
    )
    print(
        "最初の日時:",
        dataframe.iloc[0]["measured_at"],
    )
    print(
        "最後の日時:",
        dataframe.iloc[-1]["measured_at"],
    )
    print(
        "振動値一覧:",
        dataframe["vibration_value"].tolist(),
    )

    expected_values = [
        0.4,
        0.6,
        2.5,
    ]

    actual_values = (
        dataframe["vibration_value"].tolist()
    )

    if actual_values != expected_values:
        raise RuntimeError(
            "時系列順への並べ替え結果が"
            "期待値と一致しません。"
        )

    print("時系列並べ替え: 成功")


def check_missing_column(
    service,
    directory,
):
    """必須列不足を検出できるか確認する。"""

    path = write_test_file(
        directory,
        "missing_column.csv",
        MISSING_COLUMN_CSV,
    )

    try:
        service.load(path)

    except CsvRequiredColumnError as exc:
        print()
        print("必須列不足の検出: 成功")
        print("エラー内容:", str(exc))
        return

    raise RuntimeError(
        "必須列不足を検出できませんでした。"
    )


def check_invalid_datetime(
    service,
    directory,
):
    """不正な日時を検出できるか確認する。"""

    path = write_test_file(
        directory,
        "invalid_datetime.csv",
        INVALID_DATETIME_CSV,
    )

    try:
        service.load(path)

    except CsvInvalidDatetimeError as exc:
        print()
        print("不正日時の検出: 成功")
        print("エラー内容:", str(exc))
        return

    raise RuntimeError(
        "不正な日時を検出できませんでした。"
    )


def check_invalid_value(
    service,
    directory,
):
    """不正な振動値を検出できるか確認する。"""

    path = write_test_file(
        directory,
        "invalid_value.csv",
        INVALID_VALUE_CSV,
    )

    try:
        service.load(path)

    except CsvInvalidValueError as exc:
        print()
        print("不正振動値の検出: 成功")
        print("エラー内容:", str(exc))
        return

    raise RuntimeError(
        "不正な振動値を検出できませんでした。"
    )


def check_missing_value(
    service,
    directory,
):
    """欠損値を検出できるか確認する。"""

    path = write_test_file(
        directory,
        "missing_value.csv",
        MISSING_VALUE_CSV,
    )

    try:
        service.load(path)

    except CsvMissingValueError as exc:
        print()
        print("欠損値の検出: 成功")
        print("エラー内容:", str(exc))
        return

    raise RuntimeError(
        "欠損値を検出できませんでした。"
    )


def main():
    """CsvServiceの正常系と異常系を確認する。"""

    service = CsvService()

    print("=== CsvService確認 ===")

    with TemporaryDirectory() as directory:
        check_valid_csv(
            service,
            directory,
        )

        check_missing_column(
            service,
            directory,
        )

        check_invalid_datetime(
            service,
            directory,
        )

        check_invalid_value(
            service,
            directory,
        )

        check_missing_value(
            service,
            directory,
        )

    print()
    print("CsvServiceの全確認: 成功")


if __name__ == "__main__":
    try:
        main()

    except CsvServiceError as exc:
        print(
            "CsvService確認失敗:",
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
