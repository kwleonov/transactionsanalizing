# the test_services module

import json
from unittest.mock import patch

import pandas as pd
import pytest

from src.services import search_individual_transfers


def test_search_individual_transfers() -> None:
    """testing search_individual_transfers"""

    with patch("pandas.read_excel") as mock_excel:
        mock_excel.return_value = pd.DataFrame(
            [
                (
                    "31.12.2021 00:12:53", "31.12.2021", "", "OK",
                    -800.0, "RUB", -800.0, "RUB", 0.0,
                    "Переводы", 0, "Константин Л.", 0, 0, 800.0,
                ),
                (
                    "31.12.2021 00:12:54", "31.12.2021", "", "FAILED",
                    -800.0, "RUB", -800.0, "RUB", 0.0,
                    "Переводы", 0, "Константин Л.", 0, 0, 800.0,
                ),
                (
                    "31.12.2021 00:12:55", "31.12.2021", "", "OK",
                    800.0, "RUB", 800.0, "RUB", 0.0,
                    "Переводы", 0, "Константин Л.", 0, 0, 800.0,
                ),
                (
                    "31.12.2021 00:12:56", "31.12.2021", "", "OK",
                    -800.0, "RUB", -800.0, "RUB", 0.0,
                    "Оплата", 0, "Константин Л.", 0, 0, 800.0,
                ),
                (
                    "31.12.2021 00:12:57", "31.12.2021", "", "OK",
                    -800.0, "RUB", -800.0, "RUB", 0.0,
                    "Оплата", 0, "Константин Ли", 0, 0, 800.0,
                ),
            ],
            columns=[
                "Дата операции",
                "Дата платежа",
                "Номер карты",
                "Статус",
                "Сумма операции",
                "Валюта операции",
                "Сумма платежа",
                "Валюта платежа",
                "Кэшбэк",
                "Категория",
                "MCC",
                "Описание",
                "Бонусы (включая кэшбэк)",
                "Округление на инвесткопилку",
                "Сумма операции с округлением",
            ]
        )
        result = [
            {
                "operation_date": "31.12.2021 00:12:53",
                "payment_date": "31.12.2021",
                "card_number": "",
                "status": "OK",
                "operation_amount": -800.0,
                "operation_currency": "RUB",
                "payment_amount": -800.0,
                "payment_currency": "RUB",
                "cashback": 0,
                "category": "Переводы",
                "MCC": 0,
                "description": "Константин Л.",
                "bonus_with_cashback": 0,
                "round_for_invest_monybox": 0,
                "round_amount": 800.0,
            },
        ]

        transactions_str = search_individual_transfers()
        transactions = json.loads(transactions_str)

        assert transactions == result


def test_search_individual_transfers_empty_excel() -> None:
    """testing getting empty excel data"""

    with patch("pandas.read_excel") as mock_excel:
        mock_excel.return_value = pd.DataFrame()
        transactions_str = search_individual_transfers()
        assert transactions_str == ""


def test_search_individual_transfers_empty_filtered() -> None:
    """testing getting empty data after filtered"""

    with patch("pandas.read_excel") as mock_excel:
        mock_excel.return_value = pd.DataFrame(

            [
                (
                    "31.12.2021 00:12:54", "31.12.2021", "", "FAILED",
                    -800.0, "RUB", -800.0, "RUB", 0.0,
                    "Переводы", 0, "Константин Л.", 0, 0, 800.0,
                ),
                (
                    "31.12.2021 00:12:55", "31.12.2021", "", "OK",
                    800.0, "RUB", 800.0, "RUB", 0.0,
                    "Переводы", 0, "Константин Л.", 0, 0, 800.0,
                ),
                (
                    "31.12.2021 00:12:56", "31.12.2021", "", "OK",
                    -800.0, "RUB", -800.0, "RUB", 0.0,
                    "Оплата", 0, "Константин Л.", 0, 0, 800.0,
                ),
            ],
            columns=[
                "Дата операции",
                "Дата платежа",
                "Номер карты",
                "Статус",
                "Сумма операции",
                "Валюта операции",
                "Сумма платежа",
                "Валюта платежа",
                "Кэшбэк",
                "Категория",
                "MCC",
                "Описание",
                "Бонусы (включая кэшбэк)",
                "Округление на инвесткопилку",
                "Сумма операции с округлением",
            ]
        )
        transactions_str = search_individual_transfers()
        assert transactions_str == ""


@pytest.mark.parametrize("df", [
    pd.DataFrame([("31.12.2021")], columns=["Дата платежа"]),
    pd.DataFrame(
        [("OK", "Переводы", -800.0)],
        columns=["Статус", "Категория", "Сумма платежа"]),
])
def test_search_individual_transfers_key_error(df: pd.DataFrame) -> None:
    """testing getting key error"""

    with patch("pandas.read_excel") as mock_excel:
        mock_excel.return_value = df
        transactions_str = search_individual_transfers()
        assert transactions_str == ""
