import datetime
from enum import Enum
from typing import Optional

from pydantic.dataclasses import dataclass

FilmWorkId = str
PersonId = str
GenreId = str


@dataclass(frozen=True)
class FilmWork:
    """FilmWork модель."""

    id: FilmWorkId
    title: str
    description: Optional[str]
    creation_date: Optional[datetime.datetime]
    file_path: Optional[str]
    rating: Optional[float]
    type: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


@dataclass(frozen=True)
class Genre:
    """Genre модель."""

    id: GenreId
    name: str
    description: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime


@dataclass(frozen=True)
class Person:
    """Person модель."""

    id: PersonId
    full_name: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


@dataclass(frozen=True)
class GenreFilmWork:
    """GenreFilmWork модель."""

    id: str
    film_work_id: FilmWorkId
    genre_id: str
    created_at: datetime.datetime


@dataclass(frozen=True)
class PersonFilmWork:
    """PersonFilmWork модель."""

    id: str
    film_work_id: FilmWorkId
    person_id: PersonId
    role: str
    created_at: datetime.datetime


@dataclass(frozen=True)
class RoleType(str, Enum):
    """Поле, обозначающее роль участника фильма."""

    actor = 'actor'
    writer = 'writer'
    director = 'director'
