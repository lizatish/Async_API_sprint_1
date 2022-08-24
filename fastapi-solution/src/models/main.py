from typing import List, Optional, Literal

from pydantic import BaseModel, Field

from models.common import UUIDMixin


class PersonFilm(BaseModel):
    role: Literal['actor', 'writer', 'director']
    film_ids: List[str]


class Person(UUIDMixin):
    """Модель персонажа."""

    full_name: str = Field(..., alias='name')
    films: List[Optional[PersonFilm]] = []


class Genre(UUIDMixin):
    """Модель жанра."""

    name: str
    description: Optional[str]


class Film(UUIDMixin):
    """Модель кинопроизведения."""

    title: str
    imdb_rating: float
    description: Optional[str]
    genre: List[Genre] = []
    actors: List[Person] = []
    writers: List[Person] = []
    directors: List[Person] = []
    age_limit: int = 0
