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
    @classmethod
    def get_values(cls):
        return [e.value for e in cls]


class FilterSimpleValues(BaseFilter):
    id = 'id'
    imdb_rating = 'imdb_rating'
    title = 'title'
    description = 'description'


class FilterNestedValues(BaseFilter):
    genres_names = 'genres_names'
    directors_names = 'directors_names'
    actors_names = 'actors_names'
    writers_names = 'writers_names'
    genres = 'genres'
    actors = 'actors'
    writers = 'writers'
    directors = 'directors'
