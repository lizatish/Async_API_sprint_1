from typing import List, Optional, Literal

from pydantic import BaseModel


class PersonFilm(BaseModel):
    """Вложенная модель для описания фильмов по персоне."""

    role: Literal['actor', 'writer', 'director']
    film_ids: List[str]


class Person(BaseModel):
    """Модель фильма для ответа пользователю."""

    uuid: str
    full_name: str
    films: List[Optional[PersonFilm]] = []


class FilmByPerson(BaseModel):
    """Модель для представления получения фильмов по персоне."""

    uuid: str
    title: str
    imdb_rating: float
