import datetime


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
