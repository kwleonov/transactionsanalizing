import datetime
import json
import os
from collections.abc import Callable
from typing import TypedDict
from xml.etree import ElementTree as ET

import pandas as pd
import requests
from dotenv import load_dotenv

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
Currency = TypedDict("Currency", {
    "currency": str,
    "rate": float,
})
SandP500 = TypedDict("SandP500", {
    "stock": str,
    "price": float,
})
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


def get_date(date_str: str) -> datetime.date | None:
    """convert date from str with format '%d.%m.%Y' to dict['date': datetime.date, 'time': datetime.time]"""

    try:
        date = datetime.datetime.strptime(date_str, "%d.%m.%Y")
        return date.date()
    except Exception as e:
        print(f"get_date was executed with error: {e}")
    return None


def greeting(time: datetime.time) -> str:
    """greeting by time:
    from 0 to 5:59 - Доброй ночи
    from 6 to 11:59 - Доброе утро
    from 12 to 17:59 - Добрый день
    from 18 to 23:59 - Добрый вечер"""

    good_day = "Добрый день"
    good_morning = "Доброе утро"
    good_evening = "Добрый вечер"
    good_night = "Доброй ночи"

    if time.hour < 6:
        return good_night
    if time.hour < 12:
        return good_morning
    if time.hour < 18:
        return good_day
    return good_evening


def get_currency_rates(inner: INNER) -> OUTER:
    """get exchange from currency amount by code 'currency_code' to RUB"""

    currency_rates: dict[datetime.date, dict[str, float]] = (
        dict()
    )  # dict of currency rate by date as key

    def wrapper(currency_code: str, date: datetime.date) -> float | None:
        """getting currency rates from external API"""

        if date in currency_rates:
            if currency_code in currency_rates[date]:
                return currency_rates[date][currency_code]
            print(
                f"get_currency_rates didn't find {currency_code} in {currency_rates} at {date}"
            )
            return None

        currency_rates_by_inner = inner(date)
        if currency_rates_by_inner is None:
            print(f"get_currency_rates at {date} was executed inner and returned None")
            return None

        currency_rates[date] = currency_rates_by_inner
        if currency_code in currency_rates_by_inner:
            return currency_rates_by_inner[currency_code]
        print(
            f"get_currency_rates didn't find {currency_code} in {currency_rates} at {date}"
        )
        return None

    return wrapper


@get_currency_rates
def get_currency_rates_by_cbr(date: datetime.date) -> dict[str, float] | None:
    """get currency rates by cbr.ru
    url example: 'https://cbr.ru/scripts/XML_daily.asp?date_req=21/03/2002'
    API returned XML data, where 'Valute' tag contents:
    'CharCode' as currency code, 'VunitRate' as currency rate"""

    # get XML data
    url = f'https://cbr.ru/scripts/XML_daily.asp?date_req={date.strftime("%d/%m/%Y")}'

    xml_data: ET.Element = ET.Element("Empty")
    try:
        req = requests.get(url)
        xml_data = ET.fromstring(req.content)

    except Exception as e:
        print(f"get_currency_rates_by_cbr was executed with error: {e}")
        return None

    # get currency rates from xml data
    currency_rates: dict[str, float] = dict()
    try:
        for valute in xml_data.iter("Valute"):
            charcode = valute.find("CharCode")
            rate = valute.find("VunitRate")
            if (charcode is not None) and (rate is not None):
                rate_float = float(str(rate.text).replace(",", "."))
                currency_rates[str(charcode.text)] = rate_float
    except Exception as e:
        print(f"get_currency_rates_by_cbr getting error: {e}")
        return None

    return currency_rates


def mask_card(card_number: str) -> str:
    """masking card number by template 'XXXX',
    where XXXX is last 4 digits of the card number"""

    last_digits = card_number[-4:]

    return last_digits


def read_excel(filename: str) -> pd.DataFrame:
    """reading transactions data from Excel file 'filename' and
    return pandas DataFrame or empty data if it was executed with errors."""

    excel_data = pd.DataFrame()
    try:
        with open(filename, "rb") as excel_file:
            excel_data = pd.read_excel(excel_file)
            return excel_data
    except Exception as e:
        print(f"read_excel() was executed with error: {e}")
    return excel_data


def exchange(
    amount: float, currency_code: str, date_str: str, get_currency_rate: OUTER
) -> float | None:
    """exchange amount form currency code to RUB"""

    if currency_code == "RUB":
        return amount
    date = get_date(date_str)
    if date is None:
        print("exchange was executed with error: invalid date format")
        return None
    rate = get_currency_rate(currency_code, date)
    if rate is None:
        print("exchange was executed with error: get_currency_rate was returned None")
        return None
    amount_rub = rate * amount
    return amount_rub


def get_cards_info(
    df: pd.DataFrame, date: datetime.date, get_currency_rate: OUTER
) -> list[CardType]:
    """getting list of number card and total spent"""

    cards: list[CardType] = list()
    try:
        date_end = date
        date_start = date.replace(day=1)
        df['datetime'] = df['Дата платежа'].apply(lambda x: datetime.datetime.strptime(x, "%d.%m.%Y"))
        transactions_data = df.loc[
            (df["datetime"].dt.date >= date_start)
            & (df["datetime"].dt.date <= date_end)
            & (df["Сумма платежа"] < 0)
            & (df["Статус"] == "OK"),
            [
                "Номер карты",
                "Сумма платежа",
                "Валюта платежа",
                "Дата платежа",
                "Кэшбэк",
            ],
        ].copy()

        transactions_data["amount"] = transactions_data.apply(
            lambda x: exchange(
                x["Сумма платежа"],
                x["Валюта платежа"],
                x["Дата платежа"],
                get_currency_rate,
            ),
            axis=1,
        )
        transactions_data["cashback"] = transactions_data.apply(
            lambda x: exchange(
                x["Кэшбэк"], x["Валюта платежа"], x["Дата платежа"], get_currency_rate
            ),
            axis=1,
        )
        grouped = transactions_data[["Номер карты", "amount", "cashback"]].groupby(
            "Номер карты"
        )
        cards_sum = grouped.sum().to_dict("index")
        for k, v in cards_sum.items():
            cards.append(
                {
                    "last_digits": mask_card(str(k)),
                    "total_spent": -v["amount"],
                    "cashback": v["cashback"],
                }
            )
    except Exception as e:
        print(f"get_cards_info was executed with error: {e}")
    return cards


def get_top_transactions(
    df: pd.DataFrame, date: datetime.date, get_currency_rate: OUTER
) -> list[Transaction]:
    """getting top 5 transactions by 'Сумма платежа'"""

    transactions: list[Transaction] = list()

    try:
        date_end = date
        date_start = date.replace(day=1)
        df['datetime'] = df['Дата платежа'].apply(lambda x: datetime.datetime.strptime(x, "%d.%m.%Y"))
        transactions_data = df.loc[
            (df["datetime"].dt.date >= date_start)
            & (df["datetime"].dt.date <= date_end)
            & (df["Статус"] == "OK"),
            [
                "Сумма платежа",
                "Валюта платежа",
                "Дата платежа",
                "Категория",
                "Описание",
            ],
        ].copy()
        transactions_data["amount_rub"] = transactions_data.apply(
            lambda x: exchange(
                x["Сумма платежа"],
                x["Валюта платежа"],
                x["Дата платежа"],
                get_currency_rate,
            ),
            axis=1,
        )
        transactions_data["amount_rub"] = abs(transactions_data["amount_rub"])
        top5_transactions = (
            transactions_data.rename(
                columns={
                    "Дата платежа": "date",
                    "Сумма платежа": "amount",
                    "Категория": "category",
                    "Описание": "description",
                }
            )
            .sort_values("amount_rub", ascending=False)
            .head(5)
        )
        top5_dict = top5_transactions.to_dict("records")
        for row in top5_dict:
            transactions.append(
                {
                    "date": row["date"],
                    "amount": row["amount"],
                    "category": row["category"],
                    "description": row["description"],
                }
            )

    except Exception as e:
        print(f"get_top_transactions was executed with error: {e}")

    return transactions


def get_user_prefer_currency_rates(
        user_prefer_currency: list[str], get_currency_rate: OUTER) -> list[Currency]:
    """getting user currency (from user_settings file) rates and return them in list of dict """

    rates: list[Currency] = list()
    date = datetime.date.today()
    for currency in user_prefer_currency:
        rate = get_currency_rate(currency, date)
        rate_float = 0.0
        if rate is not None:
            rate_float = float(rate)
        rates.append({"currency": currency, "rate": rate_float})
    return rates


def get_user_stocks() -> list[SandP500]:
    """getting S&P500 stocks from https://financialmodelingprep.com/api/v3/stock/list?apikey={api_key}"""

    user_stocks: list[SandP500] = list()
    try:
        stocks = list()
        load_dotenv()
        api_key = os.getenv("APISP500")
        with open("user_settings.json") as f:
            json_data = json.load(f)
            stocks = json_data["user_stocks"]

        url = f"https://financialmodelingprep.com/api/v3/stock/list?apikey={api_key}"
        resp = requests.get(url)

        if not resp.ok:
            print(f"get_user_stocks was executed with error get data from {url}: {resp.json()}")
            return user_stocks

        stocks_data = resp.json()
        for symbol in stocks_data:
            stock = symbol["symbol"]
            if stock in stocks:
                user_stocks.append({"stock": stock, "price": float(symbol["price"])})
    except Exception as e:
        print(f"get_user_stocks was executed with error: {e}")

    return user_stocks


def main_page(date_str: str = "") -> str:
    """get date by str with format 'YYYY-MM-DD HH:MM:SS'
    returns json data:
    {
        "greeting": "Добрый день",
        "cards": [
            {
                "last_digits": "1234",
                "total_spent": 1000.0,
                "cashback": 100.0,
            },
        ]
        "top_transactions": [
            {
                "date": "31.12.2024",
                "amount": 1234.56,
                "category": "Перевод",
                "description": "Покупка",
            },
        ],
        "currency_rates": [
            {
                "currency": "USD",
                "rate": float,
            },
        ],
        "stock_prices": [
            {
                "stock": "AMZN":
                "price": 3173.18,
            },
        ],
    }"""

    json_str = "{}"
    date_now = datetime.datetime.now()
    date = date_now.date()

    try:
        if date_str != "":
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()
        json_data: TransactionInfo = dict()  # type: ignore
        json_data["greeting"] = greeting(date_now.time())
        df = pd.DataFrame()
        with open("data/operations.xlsx", "rb") as f:
            df = pd.read_excel(f)
        json_data["cards"] = get_cards_info(df, date, get_currency_rates_by_cbr)
        json_data["top_transactions"] = get_top_transactions(df, date, get_currency_rates_by_cbr)

        with (open("user_settings.json") as user_settings_json_file):
            user_prefer_currencies = json.load(user_settings_json_file)["user_currencies"]
            json_data["currency_rates"] = get_user_prefer_currency_rates(
                user_prefer_currencies, get_currency_rates_by_cbr)

        json_str = json.dumps(json_data, indent=4, ensure_ascii=False)

    except Exception as e:
        print(f"main_page was executed with error: {e}")

    return json_str
