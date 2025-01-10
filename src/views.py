import datetime
import json
import logging
import os
from collections.abc import Callable
from typing import TypedDict

import pandas as pd
import requests
from dotenv import load_dotenv

from src.utils import (exchange, get_currency_rates_by_cbr, get_user_settings,
                       mask_card, read_excel)

log_file = "logs/views.log"
log_ok_str = "was executed without errors"
os.makedirs("logs", exist_ok=True)
logger = logging.getLogger(__name__)
file_formatter = logging.Formatter(
    "%(asctime)s %(filename)s %(levelname)s: %(message)s"
)
file_handler = logging.FileHandler(log_file, mode="w")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)


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

    logger.debug(f"greeting {log_ok_str}")
    if time.hour < 6:
        return good_night
    if time.hour < 12:
        return good_morning
    if time.hour < 18:
        return good_day
    return good_evening


def get_cards_info(
    df: pd.DataFrame, date: datetime.date, get_currency_rate: OUTER
) -> list[CardType]:
    """getting list of number card and total spent"""

    cards: list[CardType] = list()
    try:
        date_end = date
        date_start = date.replace(day=1)
        df["payment_date"] = pd.to_datetime(df["Дата платежа"], format='%d.%m.%Y').dt.date
        transactions_data = df.loc[
            (df["payment_date"] >= date_start)
            & (df["payment_date"] <= date_end)
            & (df["Сумма платежа"] < 0)
            & (df["Статус"] == "OK"),
            [
                "Номер карты",
                "Сумма платежа",
                "Валюта платежа",
                "Дата платежа",
                "payment_date",
                "Кэшбэк",
            ],
        ]
        if transactions_data.empty:
            logger.warning("get_cards_info got empty dataframe after filtering")
            return cards
        transactions_data["amount"] = transactions_data.apply(
            lambda x: exchange(
                x["Сумма платежа"],
                x["Валюта платежа"],
                x["payment_date"],
                get_currency_rate,
            ),
            axis=1,
        )
        transactions_data["cashback"] = transactions_data.apply(
            lambda x: exchange(
                x["Кэшбэк"], x["Валюта платежа"], x["payment_date"], get_currency_rate
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
        logger.debug(f"get_cards_info {log_ok_str}")
    except Exception as e:
        logger.error(f"get_cards_info was executed with error: {e}")
    return cards


def get_top_transactions(
    df: pd.DataFrame, date: datetime.date, get_currency_rate: OUTER
) -> list[Transaction]:
    """getting top 5 transactions by 'Сумма платежа'"""

    transactions: list[Transaction] = list()

    try:
        date_end = date
        date_start = date.replace(day=1)
        df["payment_date"] = pd.to_datetime(df["Дата платежа"], format='%d.%m.%Y').dt.date
        transactions_data = df.loc[
            (df["payment_date"] >= date_start)
            & (df["payment_date"] <= date_end)
            & (df["Статус"] == "OK"),
            [
                "Сумма платежа",
                "Валюта платежа",
                "Дата платежа",
                "payment_date",
                "Категория",
                "Описание",
            ],
        ]
        if transactions_data.empty:
            logger.warning("get_top_transactions got empty dataframe after filtering.")
            return transactions
        transactions_data["amount_rub"] = transactions_data.apply(
            lambda x: exchange(
                x["Сумма платежа"],
                x["Валюта платежа"],
                x["payment_date"],
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
        logger.debug(f"get_top_transactions {log_ok_str}")
    except Exception as e:
        logger.error(f"get_top_transactions was executed with error: {e}")

    return transactions


def get_user_prefer_currency_rates(
    user_prefer_currency: list[str], get_currency_rate: OUTER
) -> list[Currency]:
    """getting user currency (from user_settings file) rates and return them in list of dict"""

    rates: list[Currency] = list()
    date = datetime.date.today()
    for currency in user_prefer_currency:
        rate = get_currency_rate(currency, date)
        rate_float = 0.0
        if rate is not None:
            rate_float = float(rate)
        rates.append({"currency": currency, "rate": rate_float})
    logger.debug(f"get_user_prefer_currency_rates {log_ok_str}")
    return rates


def get_user_stocks(stocks: list[str]) -> list[SandP500]:
    """getting S&P500 stocks from https://financialmodelingprep.com/api/v3/stock/list?apikey={api_key}"""

    user_stocks: list[SandP500] = list()
    try:
        load_dotenv()
        api_key = os.getenv("APISP500")

        url = f"https://financialmodelingprep.com/api/v3/stock/list?apikey={api_key}"
        resp = requests.get(url)

        if not resp.ok:
            logger.warning(
                f"get_user_stocks was executed with error get data from {url}: {resp.json()}"
            )
            return user_stocks

        stocks_data = resp.json()
        for symbol in stocks_data:
            stock = symbol["symbol"]
            if stock in stocks:
                user_stocks.append({"stock": stock, "price": float(symbol["price"])})
        logger.debug(f"get_user_stocks {log_ok_str}")
    except Exception as e:
        logger.error(f"get_user_stocks was executed with error: {e}")

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
        greeting_str = greeting(date_now.time())

        df = read_excel("data/operations.xlsx")
        cards = get_cards_info(df, date, get_currency_rates_by_cbr)

        top_transactions = get_top_transactions(
            df, date, get_currency_rates_by_cbr
        )
        user_settings = get_user_settings("user_settings.json")
        if user_settings is None:
            logger.error("the main_page was executed with error: can't read user_settings.json")
            return json_str
        user_prefer_currencies = user_settings["user_currencies"]
        currency_rates = get_user_prefer_currency_rates(
            user_prefer_currencies, get_currency_rates_by_cbr
        )

        user_stocks = user_settings["user_stocks"]
        stock_prices = get_user_stocks(user_stocks)

        json_data: TransactionInfo = {
            "greeting": greeting_str,
            "cards": cards,
            "top_transactions": top_transactions,
            "currency_rates": currency_rates,
            "stock_prices": stock_prices,
        }

        json_str = json.dumps(json_data, indent=4, ensure_ascii=False)
        logger.debug(f"main_page {log_ok_str}")

    except Exception as e:
        logger.error(f"main_page was executed with error: {e}")

    return json_str
