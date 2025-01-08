# the test_reports module
import datetime as dt
from unittest.mock import call, mock_open, patch

import pandas as pd
import pytest

from src.reports import spending_by_category, write_report


@pytest.mark.parametrize(
    "data, category, json_data, date",
    [
        (
            pd.DataFrame(
                [("08.01.2025", "OK", -800.0, "Переводы")],
                columns=["Дата платежа", "Статус", "Сумма Платежа", "Категория"],
            ),
            "Переводы",
            [
                call("["),
                call("{"),
                call('"Дата платежа"'),
                call(": "),
                call('"08.01.2025"'),
                call(", "),
                call('"Статус"'),
                call(": "),
                call('"OK"'),
                call(", "),
                call('"Сумма Платежа"'),
                call(": "),
                call("-800.0"),
                call(", "),
                call('"Категория"'),
                call(": "),
                call('"Переводы"'),
                call("}"),
                call("]"),
            ],
            None,
        ),
        (
            pd.DataFrame(
                [("08.01.2025", "OK", -800.0, "Переводы")],
                columns=["Дата платежа", "Статус", "Сумма Платежа", "Категория"],
            ),
            "Переводы",
            [
                call("["),
                call("{"),
                call('"Дата платежа"'),
                call(": "),
                call('"08.01.2025"'),
                call(", "),
                call('"Статус"'),
                call(": "),
                call('"OK"'),
                call(", "),
                call('"Сумма Платежа"'),
                call(": "),
                call("-800.0"),
                call(", "),
                call('"Категория"'),
                call(": "),
                call('"Переводы"'),
                call("}"),
                call("]"),
            ],
            "2025-01-08",
        ),
    ],
)
def test_spending_by_category(
    data: pd.DataFrame, category: str, json_data: list[str], date: str | None
) -> None:
    """testing the spending_by_category function"""

    m = mock_open()
    with patch("builtins.open", m):
        spending_by_category(data, category, date)
    today = dt.date.today().strftime("%Y-%m-%d")
    m.assert_called_once_with(f"data/spending_by_category_{today}.json", "w")
    handle = m()
    handle.write.assert_has_calls(json_data)


def test_test_spending_by_category_bad_filename() -> None:
    """testing writing report by bad path to json file"""

    bad_filename = "not_exist_dir/filename.json"

    @write_report(bad_filename)
    def test_report() -> pd.DataFrame:
        """empty function for testing write_report decorator"""

        return pd.DataFrame()

    with patch("logging.Logger.error") as mock_logger:
        test_report()
        mock_logger.assert_called_once()


@pytest.mark.parametrize(
    "data, category",
    [
        (
            pd.DataFrame(
                [("2025-01-08", "OK", -800.0, "Переводы")],
                columns=["Дата платежа", "Статус", "Сумма Платежа", "Категория"],
            ),
            "Переводы",
        ),
        (
            pd.DataFrame(
                [("08.01.2025", "OK", -800.0, "Переводы")],
                columns=["Дата платежа", "Статус", "Сумма_Платежа", "Категория"],
            ),
            "Переводы",
        ),
    ],
)
def test_test_test_spending_by_category_bad_dataframe(
    data: pd.DataFrame, category: str
) -> None:
    """testing the spending_by_category function getting bad excel data"""

    with patch("logging.Logger.error") as mock_logger:
        patch_open = patch("builtins.open")
        patch_open.start()
        spending_by_category(data, category)
        patch_open.stop()
        mock_logger.assert_called_once()
