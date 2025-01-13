# The services module.

import json
import logging
import re
from os import makedirs
from typing import TypedDict

Transaction = TypedDict(
    "Transaction",
    {
        "Дата операции": str,
        "Дата платежа": str,
        "Номер карты": str,
        "Статус": str,
        "Сумма операции": float,
        "Валюта операции": str,
        "Сумма платежа": float,
        "Валюта платежа": str,
        "Кэшбэк": float,
        "Категория": str,
        "MCC": int,
        "Описание": str,
        "Бонусы (включая кэшбэк)": float,
        "Округление на инвесткопилку": float,
        "Сумма операции с округлением": float,
    },
)

log_file = "logs/services.log"
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


def search_individual_transfers(transactions: list[Transaction]) -> str:
    """returns transactions for transfers to individuals by JSON format or empty str.
    Категория: Переводы
    Описание: the field contains the first name and
              the first letter of last name of the individual
              (Константин Л.)"""

    if len(transactions) == 0:
        logger.warning("search_individual_transfers got empty transaction data.")
        return ""

    filtered_transactions: list[Transaction] = list()
    name_match = re.compile("[А-ЯA-Z][а-яa-z]* [А-ЯA-Z][.]")
    try:
        for transaction in transactions:
            if transaction["Статус"] != "OK":
                continue
            if transaction["Категория"] != "Переводы":
                continue
            if transaction["Сумма платежа"] >= 0:
                continue
            if name_match.match(transaction["Описание"]) is None:
                continue
            filtered_transactions.append(transaction)
    except Exception as e:
        logger.error(f"search_individual_transfers was executed with error: {e}.")
        return ""

    if len(filtered_transactions) == 0:
        logger.warning(
            "search_individual_transfers received empty transaction data after filtering."
        )
        return ""

    transactions_json = json.dumps(filtered_transactions, ensure_ascii=False)
    logger.debug(f"search_individual_transfers {log_ok_str}")

    return transactions_json
