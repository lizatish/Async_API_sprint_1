from datetime import date
from typing import List, Literal
from uuid import UUID

import orjson
from pydantic import BaseModel, Field, FilePath


def orjson_dumps(v, *, default):
    """Функция-подмена для быстрой работы c json."""
    return orjson.dumps(v, default=default).decode()


class UUIDMixin(BaseModel):
    """Базовая модель."""

    uuid: UUID = Field(..., alias='id')

    class Config:
        """Доп. конфигурации для базовой модели."""

        allow_population_by_field_name = True
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class Person(UUIDMixin):
    """Модель персонажа."""

    full_name: str = Field(..., alias='name')
    films_ids: List[str] = []
    role: Literal['actor', 'writer', 'director', ''] = ''


class Genre(UUIDMixin):
    """Модель жанра."""

    name: str = ''
    description: str = ''


class Film(UUIDMixin):
    """Модель кинопроизведения."""

    title: str = ''
    imdb_rating: float = 0.0
    description: str = ''
    genre: List[Genre] = []
    actors: List[Person] = []
    writers: List[Person] = []
    directors: List[Person] = []
    creation_date: date = None
    age_limit: int = 0
    file: FilePath = None
    type: Literal['movie', 'tv_show', ''] = ''
