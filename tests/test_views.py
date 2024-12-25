import datetime

import pytest

from src.views import greeting


@pytest.mark.parametrize("time_int, greeting_str", [
    (8, "Доброе утро"),
    (13, "Добрый день"),
    (20, "Добрый вечер"),
    (4, "Доброй ночи"),
])
def test_greeting(time_int: int, greeting_str: str) -> None:
    """testing greeting(time)"""

    time = datetime.time(hour=time_int)
    assert greeting(time) == greeting_str
