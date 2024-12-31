import datetime
import json
from collections.abc import Callable
from typing import TypedDict
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.views import (exchange, get_cards_info, get_currency_rates,
                       get_currency_rates_by_cbr, get_date,
                       get_top_transactions, greeting, main_page, mask_card,
                       read_excel)

INNER = Callable[[datetime.date], dict[str, float] | None]
OUTER = Callable[[str, datetime.date], float | None]
CardType = TypedDict('CardType', {
    'last_digits': str,
    'total_spent': float,
    'cashback': float
})
Transaction = TypedDict('Transaction', {
    "date": str,
    "amount": float,
    "category": str,
    "description": str,
})


@pytest.mark.parametrize("time_int, greeting_str", [
    (8, "Доброе утро"),
    (13, "Добрый день"),
    (20, "Добрый вечер"),
    (4, "Доброй ночи"),
])
def test_greeting(time_int: int, greeting_str: str) -> None:
    """testing greeting(time)"""

    time = datetime.time(hour=time_int)
    assert greeting(time) == greeting_str


@pytest.mark.parametrize("date_str, date", [
    ("30.12.2024", datetime.date(year=2024, month=12, day=30)),
    ("29.02.2001", None),
    ("31.06.2000", None),
    ("01.21.1999", None),
])
def test_get_date(date_str: str, date: datetime.date) -> None:
    """testing convert date from str to datetime.date"""

    assert date == get_date(date_str)


@pytest.mark.parametrize("date, currency, rate", [
    (datetime.date(day=30, month=12, year=2024), ['USD', 'EUR', "CYN"], [1.0, 1.0, None]),
    (datetime.date(day=10, month=12, year=2024), ['CYN', 'EUR', "USD"], [None, 2.0, 2.0]),
    (datetime.date(day=17, month=12, year=2024), ['CYN', 'EUR', "USD"], [None, None, None]),
])
def test_get_currency_rates(date: datetime.date, currency: list[str], rate: list[float | None]) -> None:
    """testing decorator"""

    def f(date: datetime.date) -> dict[str, float] | None:
        """function for testing decorator"""

        if date.day < 16:
            return {'USD': 2.0, 'EUR': 2.0}

        if date.day < 20:
            return None

        return {'USD': 1.0, 'EUR': 1.0}

    get_rate = get_currency_rates(f)
    for index in range(len(currency)):
        assert get_rate(currency[index], date) == rate[index]


def test_get_currency_rates_by_cbr() -> None:
    """testing get currency rate by cbr"""

    mock_response = """
        <ValCurse>
        <Valute>
            <CharCode>USD</CharCode>
            <VunitRate>1,0</VunitRate>
        </Valute>
        </ValCurse>
    """

    with patch('requests.get') as mock_get:
        mock_get.return_value.content = mock_response
        mock_get.return_value.status_code = 200
        result = get_currency_rates_by_cbr('USD', datetime.datetime.now().date())
        assert result == 1.0


def test_bad_xml_data() -> None:
    """testing get_currency_rates_by_cbr for getting bad xml data"""

    mock_response = """
            <ValCurse>
            <Valute>
                <CharCode>USD</CharCode>
            </Valute>
            </ValCurs>
        """

    with patch('requests.get') as mock_get:
        mock_get.return_value.content = mock_response
        mock_get.return_value.status_code = 200
        date = datetime.datetime.today()
        result = get_currency_rates_by_cbr('USD', date.replace(day=date.day-1))
        assert result is None


def test_bad_xml_rate() -> None:
    """testing get_currency_rates_by_cbr for convert bad xml data to float"""

    mock_response = """
            <ValCurse>
            <Valute>
                <CharCode>USD</CharCode>
                <VunitRate>$1</VunitRate>
            </Valute>
            </ValCurse>
        """

    with patch('requests.get') as mock_get:
        mock_get.return_value.content = mock_response
        mock_get.return_value.status_code = 200
        date = datetime.datetime.today()
        result = get_currency_rates_by_cbr('USD', date.replace(day=date.day-2))
        assert result is None


def test_mask_card() -> None:
    """testing mask_card"""

    assert mask_card('*1234') == '1234'


@patch('pandas.read_excel')
def test_read_excel(mock_read: Mock) -> None:
    """testing read excel file"""

    excel_data = pd.DataFrame([(1, 2)], columns=['a', 'b'])
    mock_read.return_value = excel_data
    read_data = read_excel('data/operations.xlsx')
    assert read_data.equals(excel_data)


def test_not_exist_excel() -> None:
    """testing get not exist excel file"""

    not_exist_excel = read_excel('notexist.xlsx')
    assert not_exist_excel.empty


@pytest.mark.parametrize("amount, currency_code, date_str, func, result", [
    (100.0, 'RUB', '01.02.2003', lambda x, y: 1.0, 100.0),
    (100.0, 'USD', '02.02.2003', lambda x, y: 2.0, 200.0),
    (100.0, 'USD', '29.02.2003', lambda x, y: 3.0, None),
    (100.0, 'USD', '01.02.2003', lambda x, y: None, None),
])
def test_exchange(amount: float, currency_code: str, date_str: str,
                  func: OUTER, result: float) -> None:
    """testing exchange"""

    result_amount = exchange(amount, currency_code, date_str, func)
    assert result_amount is None or result_amount == result


def test_get_cards_info() -> None:
    """testing get_cards_info"""

    date = datetime.date.today()
    df = pd.DataFrame([
        ("OK", "*1234", -1000.0, "RUB", "15.12.2024", 100.0),
        ("OK", "*1234", -1000.0, "RUB", "16.12.2024", 100.0),
        ("OK", "*1235", -1000.0, "RUB", "15.12.2024", 100.0),
        ],
        columns=['Статус', 'Номер карты', 'Сумма платежа', 'Валюта платежа', 'Дата платежа', 'Кэшбэк'])
    cards = [{
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
    df = pd.DataFrame([
        ("OK", "*1234", -1000.0, "XYZ", "15.12.2024", 100.0),
        ("OK", "*1234", -1000.0, "RUB", "16.12.2024", 100.0),
        ("OK", "*1235", -1000.0, "RUB", "15.12.2024", 100.0),
    ],
        columns=['Статус', 'Номер карт', 'Сумма платежа', 'Валюта платежа', 'Дата платежа', 'Кэшбэк'])
    cards: list[CardType] = []
    assert get_cards_info(df, date, lambda x, y: None) == cards


@pytest.mark.parametrize("transactions, date, get_currency_rate, result_dict", [
    (
        pd.DataFrame([
            ("OK", "*1234", 100.01, "USD", "15.12.2024", "Перевод", "Друг"),
            ("OK", "*1234", -200.01, "USD", "15.12.2024", "Перевод", "Друг"),
            ("OK", "*1234", -300.01, "USD", "15.12.2024", "Перевод", "Друг"),
            ("OK", "*1234", -50.01, "USD", "15.12.2024", "Перевод", "Друг"),
            ("OK", "*1234", 30.01, "USD", "15.12.2024", "Перевод", "Друг"),
            ("OK", "*1234", 500.01, "USD", "15.12.2024", "Перевод", "Друг"),
            ("OK", "*1234", -400.01, "USD", "15.12.2024", "Перевод", "Друг"),
        ],
            columns=[
                "Статус", "Номер карт", "Сумма платежа", "Валюта платежа", "Дата платежа", "Категория", "Описание",
            ]),
        datetime.date(day=31, month=12, year=2024),
        lambda x, y: 1.0,
        [
            {"date": "15.12.2024", "amount": 500.01, "category": "Перевод", "description": "Друг"},
            {"date": "15.12.2024", "amount": -400.01, "category": "Перевод", "description": "Друг"},
            {"date": "15.12.2024", "amount": -300.01, "category": "Перевод", "description": "Друг"},
            {"date": "15.12.2024", "amount": -200.01, "category": "Перевод", "description": "Друг"},
            {"date": "15.12.2024", "amount": 100.01, "category": "Перевод", "description": "Друг"},
        ],
    ),
])
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

    df = pd.DataFrame([
            ("OK", "*1234", 100.01, "USD", "15.12.2024", "Перевод", "Друг"),
            ("OK", "*1234", -200.01, "USD", "15.12.2024", "Перевод", "Друг"),
            ("OK", "*1234", -300.01, "USD", "15.12.2024", "Перевод", "Друг"),
            ("OK", "*1234", -50.01, "USD", "15.12.2024", "Перевод", "Друг"),
            ("OK", "*1234", 30.01, "USD", "15.12.2024", "Перевод", "Друг"),
            ("OK", "*1234", 500.01, "USD", "15.12.2024", "Перевод", "Друг"),
            ("OK", "*1234", -400.01, "USD", "15.12.2024", "Перевод", "Друг"),
        ],
            columns=[
                "Статус", "Номер карт", "Сумма платежа", "Валюта платежа", "Дата платежа", "Категори", "Описание",
            ])
    date = datetime.date.today()
    assert get_top_transactions(df, date, lambda x, y: 1.0) == []


@pytest.mark.parametrize("date, json_result", [
    ("2024-12-30 21:58:00",
     '{"greeting": "", "cards": [{"last_digits": "1234", "total_spent": 2000.0, "cashback": 200.0}]}'),
    ("2024-12-30 24:00:01", "{}"),
])
def test_main_page(date: str, json_result: str) -> None:
    """testing main_page"""

    with patch('pandas.read_excel') as mock_excel:
        mock_excel.return_value = pd.DataFrame([
            ("OK", "*1234", -1000.0, "RUB", "15.12.2024", 100.0),
            ("OK", "*1234", -1000.0, "RUB", "16.12.2024", 100.0),
            ],
            columns=['Статус', 'Номер карты', 'Сумма платежа', 'Валюта платежа', 'Дата платежа', 'Кэшбэк'])
        json_data = json.loads(json_result)
        if "greeting" in json_data:
            json_data["greeting"] = greeting(datetime.datetime.now().time())
        json_str = json.dumps(json_data, ensure_ascii=False).replace(' ', '')
        result = main_page(date).replace(' ', '').replace('\n', '')
        assert result == json_str
