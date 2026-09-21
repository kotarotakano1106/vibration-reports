from pathlib import Path

import pytest

from backend.src.services.csv_service import (
    CsvEmptyError,
    CsvFileNotFoundError,
    CsvInvalidDatetimeError,
    CsvInvalidValueError,
    CsvMissingValueError,
    CsvRequiredColumnError,
    CsvService,
)


def write_csv(
    file_path: Path,
    content: str,
    encoding: str = "utf-8",
) -> Path:
    """テスト用CSVファイルを作成する。"""

    file_path.write_text(
        content,
        encoding=encoding,
    )
    return file_path


def test_load_returns_sorted_dataframe(
    tmp_path: Path,
) -> None:
    """正常なCSVを日時の昇順で読み込める。"""

    csv_path = write_csv(
        tmp_path / "valid.csv",
        (
            "measured_at,vibration_value\n"
            "2026-09-01T10:00:02+09:00,2.5\n"
            "2026-09-01T10:00:00+09:00,1.0\n"
            "2026-09-01T10:00:01+09:00,1.5\n"
        ),
    )

    result = CsvService().load(csv_path)

    assert list(result.columns) == [
        "measured_at",
        "vibration_value",
    ]
    assert result["vibration_value"].tolist() == [
        1.0,
        1.5,
        2.5,
    ]
    assert result["measured_at"].is_monotonic_increasing


def test_load_strips_column_names(
    tmp_path: Path,
) -> None:
    """列名の前後にある空白を除去できる。"""

    csv_path = write_csv(
        tmp_path / "column_spaces.csv",
        (
            " measured_at , vibration_value \n"
            "2026-09-01T10:00:00+09:00,1.0\n"
        ),
    )

    result = CsvService().load(csv_path)

    assert list(result.columns) == [
        "measured_at",
        "vibration_value",
    ]


def test_load_raises_when_file_does_not_exist(
    tmp_path: Path,
) -> None:
    """存在しないCSVでは専用例外を送出する。"""

    csv_path = tmp_path / "not-found.csv"

    with pytest.raises(CsvFileNotFoundError):
        CsvService().load(csv_path)


def test_load_raises_when_file_is_empty(
    tmp_path: Path,
) -> None:
    """完全に空のCSVでは専用例外を送出する。"""

    csv_path = write_csv(
        tmp_path / "empty.csv",
        "",
    )

    with pytest.raises(CsvEmptyError):
        CsvService().load(csv_path)


def test_load_raises_when_csv_has_only_header(
    tmp_path: Path,
) -> None:
    """ヘッダーだけのCSVでは専用例外を送出する。"""

    csv_path = write_csv(
        tmp_path / "header-only.csv",
        "measured_at,vibration_value\n",
    )

    with pytest.raises(CsvEmptyError):
        CsvService().load(csv_path)


def test_load_raises_when_required_column_is_missing(
    tmp_path: Path,
) -> None:
    """必須列が不足したCSVでは専用例外を送出する。"""

    csv_path = write_csv(
        tmp_path / "missing-column.csv",
        (
            "measured_at\n"
            "2026-09-01T10:00:00+09:00\n"
        ),
    )

    with pytest.raises(CsvRequiredColumnError):
        CsvService().load(csv_path)


def test_load_raises_when_datetime_is_invalid(
    tmp_path: Path,
) -> None:
    """日時を変換できない場合は専用例外を送出する。"""

    csv_path = write_csv(
        tmp_path / "invalid-datetime.csv",
        (
            "measured_at,vibration_value\n"
            "invalid-datetime,1.0\n"
        ),
    )

    with pytest.raises(CsvInvalidDatetimeError):
        CsvService().load(csv_path)


def test_load_raises_when_vibration_value_is_invalid(
    tmp_path: Path,
) -> None:
    """振動値を数値へ変換できない場合は専用例外を送出する。"""

    csv_path = write_csv(
        tmp_path / "invalid-value.csv",
        (
            "measured_at,vibration_value\n"
            "2026-09-01T10:00:00+09:00,invalid-value\n"
        ),
    )

    with pytest.raises(CsvInvalidValueError):
        CsvService().load(csv_path)


@pytest.mark.parametrize(
    "csv_content",
    [
        (
            "measured_at,vibration_value\n"
            ",1.0\n"
        ),
        (
            "measured_at,vibration_value\n"
            "2026-09-01T10:00:00+09:00,\n"
        ),
    ],
)
def test_load_raises_when_required_value_is_missing(
    tmp_path: Path,
    csv_content: str,
) -> None:
    """必須項目に欠損値がある場合は専用例外を送出する。"""

    csv_path = write_csv(
        tmp_path / "missing-value.csv",
        csv_content,
    )

    with pytest.raises(CsvMissingValueError):
        CsvService().load(csv_path)
