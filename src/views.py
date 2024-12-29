import datetime
from collections.abc import Callable
from xml.etree import ElementTree as ET

import requests

INNER = Callable[[datetime.date], dict[str, float] | None]
OUTER = Callable[[str, datetime.date], float | None]


def greeting(time: datetime.time) -> str:
    """greeting by time:
    from 0 to 5:59 - Доброй ночи
    from 6 to 11:59 - Доброе утро
    from 12 to 17:59 - Добрый день
    from 18 to 23:59 - Добрый вечер"""

    good_day = 'Добрый день'
    good_morning = 'Доброе утро'
    good_evening = 'Добрый вечер'
    good_night = 'Доброй ночи'

    if time.hour < 6:
        return good_night
    if time.hour < 12:
        return good_morning
    if time.hour < 18:
        return good_day
    return good_evening


def get_currency_rates(inner: INNER) -> OUTER:
    """get exchange from currency amount by code 'currency_code' to RUB"""

    currency_rates: dict[datetime.date, dict[str, float]] = dict()  # dict of currency rate by date as key

    def wrapper(currency_code: str, date: datetime.date) -> float | None:
        """getting currency rates from external API"""

        if date in currency_rates:
            if currency_code in currency_rates[date]:
                return currency_rates[date][currency_code]
            print(f"get_currency_rates didn\'t find {currency_code} in currency_rates at {date}")
            return None

        currency_rates_by_inner = inner(date)
        if currency_rates_by_inner is None:
            print(f"get_currency_rates at {date} was executed inner and returned None")
            return None

        currency_rates[date] = currency_rates_by_inner
        if currency_code in currency_rates_by_inner:
            return currency_rates_by_inner[currency_code]
        print(f"get_currency_rates didn\'t find {currency_code} in currency_rates at {date}")
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
