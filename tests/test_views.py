import datetime
import json
from collections.abc import Callable
from typing import TypedDict
from unittest.mock import patch

import pandas as pd
import pytest

from src.views import (get_cards_info, get_top_transactions,
                       get_user_prefer_currency_rates, get_user_stocks,
                       greeting, main_page)

INNER = Callable[[datetime.date], dict[str, float] | None]
OUTER = Callable[[str, datetime.date], float | None]
CardType = TypedDict(
    "CardType", {"last_digits": str, "total_spent": float, "cashback": float}
)
Transaction = TypedDict(
    "Transaction",
    {
        "date": str,
        "amount": float,
        "category": str,
        "description": str,
    },
)
Currency = TypedDict(
    "Currency",
    {
        "currency": str,
        "rate": float,
    },
)
SandP500 = TypedDict(
    "SandP500",
    {
        "stock": str,
        "price": float,
    },
)
TransactionInfo = TypedDict(
    "TransactionInfo",
    {
        "greeting": str,
        "cards": list[CardType],
        "top_transactions": list[Transaction],
        "currency_rates": list[Currency],
        "stock_prices": list[SandP500],
    },
)


@pytest.mark.parametrize(
    "time_int, greeting_str",
    [
        (8, "Доброе утро"),
        (13, "Добрый день"),
        (20, "Добрый вечер"),
        (4, "Доброй ночи"),
    ],
)
def test_greeting(time_int: int, greeting_str: str) -> None:
    """testing greeting(time)"""

    time = datetime.time(hour=time_int)
    assert greeting(time) == greeting_str


def test_get_cards_info() -> None:
    """testing get_cards_info"""

    date = datetime.date(day=17, month=12, year=1993)
    df = pd.DataFrame(
        [
            ("OK", "*1234", -1000.0, "RUB", "15.12.1993", 100.0),
            ("OK", "*1234", -1000.0, "RUB", "16.12.1993", 100.0),
            ("OK", "*1235", -1000.0, "RUB", "15.12.1993", 100.0),
        ],
        columns=[
            "Статус",
            "Номер карты",
            "Сумма платежа",
            "Валюта платежа",
            "Дата платежа",
            "Кэшбэк",
        ],
    )
    cards = [
        {
            "last_digits": "1234",
            "total_spent": 2000.0,
            "cashback": 200.0,
        },
        {
            "last_digits": "1235",
            "total_spent": 1000.0,
            "cashback": 100.0,
        },
    ]

    assert get_cards_info(df, date, lambda x, y: 1.0) == cards


def test_get_cards_info_error() -> None:
    """testing get_cards_info with bad data"""

    date = datetime.date.today()
    df = pd.DataFrame(
        [
            ("OK", "*1234", -1000.0, "XYZ", "15.12.1994", 100.0),
            ("OK", "*1234", -1000.0, "RUB", "16.12.1994", 100.0),
            ("OK", "*1235", -1000.0, "RUB", "15.12.1994", 100.0),
        ],
        columns=[
            "Статус",
            "Номер карт",
            "Сумма платежа",
            "Валюта платежа",
            "Дата платежа",
            "Кэшбэк",
        ],
    )
    cards: list[CardType] = []
    assert get_cards_info(df, date, lambda x, y: None) == cards


@pytest.mark.parametrize(
    "transactions, date, get_currency_rate, result_dict",
    [
        (
            pd.DataFrame(
                [
                    ("OK", "*1234", 100.01, "USD", "15.12.1995", "Перевод", "Друг"),
                    ("OK", "*1234", -200.01, "USD", "15.12.1995", "Перевод", "Друг"),
                    ("OK", "*1234", -300.01, "USD", "15.12.1995", "Перевод", "Друг"),
                    ("OK", "*1234", -50.01, "USD", "15.12.1995", "Перевод", "Друг"),
                    ("OK", "*1234", 30.01, "USD", "15.12.1995", "Перевод", "Друг"),
                    ("OK", "*1234", 500.01, "USD", "15.12.1995", "Перевод", "Друг"),
                    ("OK", "*1234", -400.01, "USD", "15.12.1995", "Перевод", "Друг"),
                ],
                columns=[
                    "Статус",
                    "Номер карт",
                    "Сумма платежа",
                    "Валюта платежа",
                    "Дата платежа",
                    "Категория",
                    "Описание",
                ],
            ),
            datetime.date(day=31, month=12, year=1995),
            lambda x, y: 1.0,
            [
                {
                    "date": "15.12.1995",
                    "amount": 500.01,
                    "category": "Перевод",
                    "description": "Друг",
                },
                {
                    "date": "15.12.1995",
                    "amount": -400.01,
                    "category": "Перевод",
                    "description": "Друг",
                },
                {
                    "date": "15.12.1995",
                    "amount": -300.01,
                    "category": "Перевод",
                    "description": "Друг",
                },
                {
                    "date": "15.12.1995",
                    "amount": -200.01,
                    "category": "Перевод",
                    "description": "Друг",
                },
                {
                    "date": "15.12.1995",
                    "amount": 100.01,
                    "category": "Перевод",
                    "description": "Друг",
                },
            ],
        ),
    ],
)
def test_get_top_transactions(
    transactions: pd.DataFrame,
    date: datetime.date,
    get_currency_rate: OUTER,
    result_dict: list[Transaction],
) -> None:
    """testing get top transactions list"""

    result = get_top_transactions(transactions, date, get_currency_rate)
    assert result == result_dict


def test_get_top_transactions_error() -> None:
    """testing get_top_transactions getting error"""

    df = pd.DataFrame(
        [
            ("OK", "*1234", 100.01, "USD", "15.12.1996", "Перевод", "Друг"),
            ("OK", "*1234", -200.01, "USD", "15.12.1996", "Перевод", "Друг"),
            ("OK", "*1234", -300.01, "USD", "15.12.1996", "Перевод", "Друг"),
            ("OK", "*1234", -50.01, "USD", "15.12.1996", "Перевод", "Друг"),
            ("OK", "*1234", 30.01, "USD", "15.12.1996", "Перевод", "Друг"),
            ("OK", "*1234", 500.01, "USD", "15.12.1996", "Перевод", "Друг"),
            ("OK", "*1234", -400.01, "USD", "15.12.1996", "Перевод", "Друг"),
        ],
        columns=[
            "Статус",
            "Номер карт",
            "Сумма платежа",
            "Валюта платежа",
            "Дата платежа",
            "Категори",
            "Описание",
        ],
    )
    date = datetime.date.today()
    assert get_top_transactions(df, date, lambda x, y: 1.0) == []


@pytest.mark.parametrize(
    "user_currencies, currency_rates",
    [
        (
            ["USD", "EUR"],
            [{"currency": "USD", "rate": 100.0}, {"currency": "EUR", "rate": 100.0}],
        ),
    ],
)
def test_get_user_prefer_currency_rates(
    user_currencies: list[str], currency_rates: list[Currency]
) -> None:
    """testing get_user_prefer_currency_rates"""

    assert (
        get_user_prefer_currency_rates(user_currencies, lambda x, y: 100.0)
        == currency_rates
    )


def test_get_user_stocks() -> None:
    """testing get stocks s&p500"""

    test_result = [{"stock": "AAPL", "price": 100.0}]

    user_stocks = ["AAPL"]

    patch_requests = patch("requests.get")
    mock_requests = patch_requests.start()
    mock_requests.return_value.json.return_value = [{"symbol": "AAPL", "price": 100.0}]
    mock_requests.return_value.ok = True

    stock_prices = get_user_stocks(user_stocks)

    mock_requests.stop()

    assert stock_prices == test_result


def test_get_bad_url_user_stocks() -> None:
    """testing for bad api key"""

    error_msg = """{'Error Message': 'Invalid API KEY. Feel free to create a Free API Key or
    visit https://site.financialmodelingprep.com/faqs?search=why-is-my-api-key-invalid for more information.'}"""

    user_stocks = ["AAPL"]

    patch_requests = patch("requests.get")
    mock_requests = patch_requests.start()
    mock_requests.return_value.json.return_value = error_msg
    mock_requests.return_value.ok = False

    stock_prices = get_user_stocks(user_stocks)

    mock_requests.stop()

    assert stock_prices == []


def test_get_bad_user_stocks() -> None:
    """testing for bad json data"""

    user_stocks = ["AAPL"]

    patch_requests = patch("requests.get")
    mock_requests = patch_requests.start()
    mock_requests.return_value.json.return_value = [
        {"symbol": "AAPL", "price": "100,0"}
    ]
    mock_requests.return_value.ok = True

    stock_prices = get_user_stocks(user_stocks)

    mock_requests.stop()

    assert stock_prices == []


@pytest.mark.parametrize(
    "date, json_result",
    [
        (
            "1997-12-30 21:58:00",
            {
                "greeting": "",
                "cards": [
                    {"last_digits": "1234", "total_spent": 1800.0, "cashback": 180.0}
                ],
                "top_transactions": [
                    {
                        "date": "11.12.1997",
                        "amount": -600.0,
                        "category": "Перевод",
                        "description": "Друг",
                    },
                    {
                        "date": "15.12.1997",
                        "amount": -500.0,
                        "category": "Перевод",
                        "description": "Друг",
                    },
                    {
                        "date": "16.12.1997",
                        "amount": -400.0,
                        "category": "Перевод",
                        "description": "Друг",
                    },
                    {
                        "date": "12.12.1997",
                        "amount": -200.0,
                        "category": "Перевод",
                        "description": "Друг",
                    },
                    {
                        "date": "17.12.1997",
                        "amount": -100.0,
                        "category": "Перевод",
                        "description": "Друг",
                    },
                ],
                "currency_rates": [
                    {
                        "currency": "USD",
                        "rate": 100.0,
                    },
                    {
                        "currency": "EUR",
                        "rate": 110.0,
                    },
                ],
                "stock_prices": [
                    {
                        "stock": "AAPL",
                        "price": 100.0,
                    },
                ],
            },
        ),
        ("1998-12-30 24:00:01", {}),
    ],
)
def test_main_page(date: str, json_result: TransactionInfo) -> None:
    """testing main_page"""

    with patch("pandas.read_excel") as mock_excel:
        mock_excel.return_value = pd.DataFrame(
            [
                ("OK", "*1234", -500.0, "RUB", "15.12.1997", 50.0, "Перевод", "Друг"),
                ("OK", "*1234", -400.0, "RUB", "16.12.1997", 40.0, "Перевод", "Друг"),
                ("OK", "*1234", -100.0, "RUB", "17.12.1997", 10.0, "Перевод", "Друг"),
                ("OK", "*1234", -600.0, "RUB", "11.12.1997", 60.0, "Перевод", "Друг"),
                ("OK", "*1234", -200.0, "RUB", "12.12.1997", 20.0, "Перевод", "Друг"),
            ],
            columns=[
                "Статус",
                "Номер карты",
                "Сумма платежа",
                "Валюта платежа",
                "Дата платежа",
                "Кэшбэк",
                "Категория",
                "Описание",
            ],
        )
        if "greeting" in json_result:
            json_result["greeting"] = greeting(datetime.datetime.now().time())
        result = ""
        patch_requests = patch("requests.get")
        mock_requests = patch_requests.start()
        mock_requests.return_value.content = """
        <ValCurse>
            <Valute>
                <CharCode>USD</CharCode>
                <VunitRate>100,0</VunitRate>
            </Valute>
            <Valute>
                <CharCode>EUR</CharCode>
                <VunitRate>110,0</VunitRate>
            </Valute>
        </ValCurse>"""
        mock_requests.return_value.json.return_value = [
            {"symbol": "AAPL", "price": 100.0}
        ]
        patch_json = patch("json.load")
        mock_json = patch_json.start()
        mock_json.return_value = {
            "user_currencies": ["USD", "EUR"],
            "user_stocks": ["AAPL"],
        }

        result = main_page(date)
        patch_json.stop()
        patch_requests.stop()
        json_data = json.loads(result)
        assert json_data == json_result
