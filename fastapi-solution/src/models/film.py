from typing import List, Optional

from models.common import UUIDMixin
from models.person import Person


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
