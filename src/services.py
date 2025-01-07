# The services module.

import json

import pandas as pd

from src.utils import read_excel


def search_individual_transfers() -> str:
    """returns transactions for transfers to individuals by JSON format or empty str.
    Категория: Переводы
    Описание: the field contains the first name and
              the first letter of last name of the individual
              (Константин Л.)"""

    transactions = ""

    df = read_excel("data/operations.xlsx")
    if df.empty:
        print("search_individual_transfers got empty excel data.")
        return transactions

    filtered_df = pd.DataFrame()
    try:
        name_pattern = "[А-ЯA-Z][а-яa-z]* [А-ЯA-Z][.]"
        filtered_df = df.loc[(df["Статус"] == "OK") &
                             (df["Категория"] == "Переводы") &
                             (df["Сумма платежа"] < 0) &
                             (df["Описание"].str.match(name_pattern))]
    except Exception as e:
        print(f"search_individual_transfers was executed with error: {e}.")
        return transactions

    if filtered_df.empty:
        print("search_individual_transfers received empty transaction data after filtering.")
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

    return transactions
