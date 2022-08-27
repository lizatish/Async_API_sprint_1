import enum

import orjson
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    """Функция-подмена для быстрой работы c json."""
    return orjson.dumps(v, default=default).decode()


class UUIDMixin(BaseModel):
    """Базовая модель."""

    id: str

    class Config:
        """Доп. конфигурации для базовой модели."""

        allow_population_by_field_name = True
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class BaseFilter(enum.Enum):
    """Базовая модель фильма."""

    @classmethod
    def get_values(cls) -> list:
        """Возвращает все значения класса."""
        return [e.value for e in cls]


class FilterSimpleValues(BaseFilter):
    """Модель невложенных полей фильтра."""

    id = 'id'
    imdb_rating = 'imdb_rating'
    title = 'title'
    description = 'description'


class FilterNestedValues(BaseFilter):
    """Модель вложенных полей фильтра."""

    genres = 'genres'
    actors = 'actors'
    writers = 'writers'
    directors = 'directors'
