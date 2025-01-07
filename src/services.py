# The services module.

import json
import logging
from os import makedirs

import pandas as pd

from src.utils import read_excel

log_file = "logs/services.log"
log_ok_str = "was executed without errors"
makedirs("logs", exist_ok=True)
logger = logging.getLogger(__name__)
file_formatter = logging.Formatter("%(asctime)s %(filename)s %(levelname)s: %(message)s")
file_handler = logging.FileHandler(log_file, mode="w")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)


def search_individual_transfers() -> str:
    """returns transactions for transfers to individuals by JSON format or empty str.
    Категория: Переводы
    Описание: the field contains the first name and
              the first letter of last name of the individual
              (Константин Л.)"""

    transactions = ""

    df = read_excel("data/operations.xlsx")
    if df.empty:
        logger.warning("search_individual_transfers got empty excel data.")
        return transactions

    filtered_df = pd.DataFrame()
    try:
        name_pattern = "[А-ЯA-Z][а-яa-z]* [А-ЯA-Z][.]"
        filtered_df = df.loc[(df["Статус"] == "OK") &
                             (df["Категория"] == "Переводы") &
                             (df["Сумма платежа"] < 0) &
                             (df["Описание"].str.match(name_pattern))]
    except Exception as e:
        logger.error(f"search_individual_transfers was executed with error: {e}.")
        return transactions

    if filtered_df.empty:
        logger.warning("search_individual_transfers received empty transaction data after filtering.")
        return transactions

    transactions_dict = filtered_df.rename(
        columns={
            "Дата операции": "operation_date",
            "Дата платежа": "payment_date",
            "Номер карты": "card_number",
            "Статус": "status",
            "Сумма операции": "operation_amount",
            "Валюта операции": "operation_currency",
            "Сумма платежа": "payment_amount",
            "Валюта платежа": "payment_currency",
            "Кэшбэк": "cashback",
            "Категория": "category",
            "MCC": "MCC",
            "Описание": "description",
            "Бонусы (включая кэшбэк)": "bonus_with_cashback",
            "Округление на инвесткопилку": "round_for_invest_monybox",
            "Сумма операции с округлением": "round_amount",
        }
    ).to_dict("records")

    transactions = json.dumps(transactions_dict, ensure_ascii=False)
    logger.debug(f"search_individual_transfers {log_ok_str}")

    return transactions
