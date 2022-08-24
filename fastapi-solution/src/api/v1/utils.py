import re

from fastapi import Request


def get_page(req: Request) -> dict:
    """Функция преобразует данные для пагинации из запроса
    к необходимому виду.
    """
    number = req.query_params.get('page[number]')
    size = req.query_params.get('page[size]')
    if number and size:
        from_ = (int(number)-1) * int(size)
    else:
        from_ = 0
    return {
        "size": int(size) if size else 5,
        "from": from_
    }


def get_filter(req: Request) -> dict:
    """Функция преобразует данные для фильтрации из запроса
    к необходимому виду.
    """
    filter_ = {}
    for key, value in req.query_params.items():
        if re.match('^filter\[[a-zA-Z]{0,25}\]$', key) is not None:
            filter_[key.replace('filter[', '').replace(']', '')] = value
    return filter_
