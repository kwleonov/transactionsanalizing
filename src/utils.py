# the utils module
import datetime
import json
import logging
from collections.abc import Callable
from os import makedirs
from xml.etree import ElementTree as ET

import pandas as pd
import requests

INNER = Callable[[datetime.date], dict[str, float] | None]
OUTER = Callable[[str, datetime.date], float | None]

log_file = "logs/utils.log"
log_ok_str = "was executed without errors"
makedirs("logs", exist_ok=True)
logger = logging.getLogger(__name__)
file_formatter = logging.Formatter(
    "%(asctime)s %(filename)s %(levelname)s: %(message)s"
)
file_handler = logging.FileHandler(log_file, mode="w")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)


def read_excel(filename: str) -> pd.DataFrame:
    """reading transactions data from Excel file 'filename' and
    return pandas DataFrame or empty data if it was executed with errors."""

    excel_data = pd.DataFrame()
    try:
        with open(filename, "rb") as excel_file:
            excel_data = pd.read_excel(excel_file)
    except Exception as e:
        logger.error(f"read_excel() was executed with error: {e}")
        return excel_data

    logger.debug(f"read_excel {log_ok_str}")
    return excel_data


def get_user_settings(user_settings_json_file: str) -> dict[str, list[str]] | None:
    """getting user setting from user_settings.json"""

    try:
        with open(user_settings_json_file) as f:
            user_settings: dict[str, list[str]] = json.load(f)
            logger.debug(f"get_user_settings {log_ok_str}")
            return user_settings
    except Exception as e:
        logger.error(f"get_user_settings was executed with error: {e}")
    return None


def get_date(date_str: str) -> datetime.date | None:
    """convert date from str with format '%d.%m.%Y' to dict['date': datetime.date, 'time': datetime.time]"""

    try:
        date = datetime.datetime.strptime(date_str, "%d.%m.%Y")
        logger.debug(f"get_date {log_ok_str}")
        return date.date()
    except Exception as e:
        logger.error(f"get_date was executed with error: {e}")
    return None


def exchange(
    amount: float, currency_code: str, exchange_date: datetime.date, get_currency_rate: OUTER
) -> float | None:
    """exchange amount form currency code to RUB"""

    if currency_code == "RUB":
        return amount
    rate = get_currency_rate(currency_code, exchange_date)
    if rate is None:
        logger.warning("exchange was executed with error: get_currency_rate was returned None")
        return None
    amount_rub = rate * amount
    logger.debug(f"exchange {log_ok_str}")
    return amount_rub


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
            logger.warning(
                f"get_currency_rates didn't find {currency_code} in {currency_rates} at {date}"
            )
            return None

        currency_rates_by_inner = inner(date)
        if currency_rates_by_inner is None:
            logger.warning(f"get_currency_rates at {date} was executed inner and returned None")
            return None

        currency_rates[date] = currency_rates_by_inner
        if currency_code in currency_rates_by_inner:
            logger.debug(f"wrapper in get_currency_rate {log_ok_str}")
            return currency_rates_by_inner[currency_code]
        logger.warning(
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
        logger.error(f"get_currency_rates_by_cbr was executed with error: {e}")
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
        logger.error(f"get_currency_rates_by_cbr getting error: {e}")
        return None
    logger.debug(f"get_currency_rates_by_cbr {log_ok_str}")
    return currency_rates


def mask_card(card_number: str) -> str:
    """masking card number by template 'XXXX',
    where XXXX is last 4 digits of the card number"""

    last_digits = card_number[-4:]
    logger.debug(f"mask_card {log_ok_str}")
    return last_digits
