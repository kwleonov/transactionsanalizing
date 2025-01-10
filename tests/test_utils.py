# the test_utils module
import datetime
from collections.abc import Callable
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.utils import (exchange, get_currency_rates, get_currency_rates_by_cbr,
                       get_date, mask_card, read_excel)

INNER = Callable[[datetime.date], dict[str, float] | None]
OUTER = Callable[[str, datetime.date], float | None]


@patch("pandas.read_excel")
def test_read_excel(mock_read: Mock) -> None:
    """testing read excel file"""

    excel_data = pd.DataFrame([(1, 2)], columns=["a", "b"])
    mock_read.return_value = excel_data
    read_data = read_excel("data/operations.xlsx")
    assert read_data.equals(excel_data)


def test_not_exist_excel() -> None:
    """testing get not exist excel file"""

    not_exist_excel = read_excel("notexist.xlsx")
    assert not_exist_excel.empty


@pytest.mark.parametrize(
    "date_str, date",
    [
        ("30.12.2024", datetime.date(year=2024, month=12, day=30)),
        ("29.02.2001", None),
        ("31.06.2000", None),
        ("01.21.1999", None),
    ],
)
def test_get_date(date_str: str, date: datetime.date) -> None:
    """testing convert date from str to datetime.date"""

    assert date == get_date(date_str)


@pytest.mark.parametrize(
    "amount, currency_code, date, func, result",
    [
        (100.0, "RUB", datetime.date(day=1, month=2, year=1992), lambda x, y: 1.0, 100.0),
        (100.0, "USD", datetime.date(day=2, month=2, year=1992), lambda x, y: 2.0, 200.0),
        (100.0, "USD", datetime.date(day=1, month=2, year=1992), lambda x, y: None, None),
    ],
)
def test_exchange(
    amount: float, currency_code: str, date: datetime.date, func: OUTER, result: float
) -> None:
    """testing exchange"""

    result_amount = exchange(amount, currency_code, date, func)
    assert result_amount is None or result_amount == result


@pytest.mark.parametrize(
    "date, currency, rate",
    [
        (
            datetime.date(day=30, month=12, year=2024),
            ["USD", "EUR", "CYN"],
            [1.0, 1.0, None],
        ),
        (
            datetime.date(day=10, month=12, year=2024),
            ["CYN", "EUR", "USD"],
            [None, 2.0, 2.0],
        ),
        (
            datetime.date(day=17, month=12, year=2024),
            ["CYN", "EUR", "USD"],
            [None, None, None],
        ),
    ],
)
def test_get_currency_rates(
    date: datetime.date, currency: list[str], rate: list[float | None]
) -> None:
    """testing decorator"""

    def f(date: datetime.date) -> dict[str, float] | None:
        """function for testing decorator"""

        if date.day < 16:
            return {"USD": 2.0, "EUR": 2.0}

        if date.day < 20:
            return None

        return {"USD": 1.0, "EUR": 1.0}

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

    with patch("requests.get") as mock_get:
        mock_get.return_value.content = mock_response
        mock_get.return_value.status_code = 200
        result = get_currency_rates_by_cbr(
            "USD", datetime.date(day=1, month=2, year=1991)
        )
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

    with patch("requests.get") as mock_get:
        mock_get.return_value.content = mock_response
        mock_get.return_value.status_code = 200
        result = get_currency_rates_by_cbr(
            "USD", datetime.date(day=2, month=2, year=1991)
        )
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

    with patch("requests.get") as mock_get:
        mock_get.return_value.content = mock_response
        mock_get.return_value.status_code = 200
        result = get_currency_rates_by_cbr(
            "USD", datetime.date(day=3, month=2, year=1991)
        )
        assert result is None


def test_mask_card() -> None:
    """testing mask_card"""

    assert mask_card("*1234") == "1234"
