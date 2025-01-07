# the utils module

import logging
from os import makedirs

import pandas as pd

log_file = "logs/utils.log"
log_ok_str = "was executed without errors"
makedirs("logs", exist_ok=True)
logger = logging.getLogger(__name__)
file_formatter = logging.Formatter("%(asctime)s %(filename)s %(levelname)s: %(message)s")
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
