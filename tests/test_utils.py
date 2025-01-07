# the test_utils module

from unittest.mock import Mock, patch

import pandas as pd

from src.utils import read_excel


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
