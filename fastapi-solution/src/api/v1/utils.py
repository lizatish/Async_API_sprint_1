import re

from fastapi import Query, Request
from models.common import FilterNestedValues, FilterSimpleValues
from pydantic import BaseModel


class Paginator(BaseModel):
    """Модель для пагинации."""

    page_size: int = Query(default=50, alias='size', ge=1)
    page_number: int = Query(default=0, alias='number')


def validate_filter_values(filter_: dict) -> dict:
    """Валидирует фильтр запроса."""
    result_filter = {}

    filter_nested_values = FilterNestedValues.get_values()
    filter_simple_values = FilterSimpleValues.get_values()

    for key, val in filter_.items():
        if key in filter_nested_values or key in filter_simple_values:
            result_filter[key] = val

    return result_filter


def get_filter(req: Request) -> dict:
    """Функция преобразует данные для фильтрации из запроса  к необходимому виду."""
    filter_ = {}
    for key, value in req.query_params.items():
        if re.match('^filter\[[a-zA-Z_]{0,25}\]$', key) is not None:
            filter_[key.replace('filter[', '').replace(']', '')] = value

    return validate_filter_values(filter_)
