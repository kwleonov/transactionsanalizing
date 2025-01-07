# the utils module

import pandas as pd


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
