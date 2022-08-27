from typing import List, Optional

from pydantic import BaseModel


class Genre(BaseModel):
    """Схема жанра."""

    uuid: str
    name: str


class Persons(BaseModel):
    """Схема персоны."""

    uuid: str
    full_name: str


class Film(BaseModel):
    """Схема фильма."""

    uuid: str
    title: str
    imdb_rating: float
    description: Optional[str]
    genre: List[Genre] = []
    actors: List[Persons] = []
    writers: List[Persons] = []
    directors: List[Persons] = []


class ShortFilm(BaseModel):
    """Схема урезанной версии фильма."""

    uuid: str
    title: str
    imdb_rating: float
