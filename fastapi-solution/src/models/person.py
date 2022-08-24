from typing import List, Literal, Optional

from pydantic import Field, BaseModel

from models.common import UUIDMixin


class PersonFilm(BaseModel):
    role: Literal['actor', 'writer', 'director']
    film_ids: List[str]


class Person(UUIDMixin):
    """Модель персонажа."""

    full_name: str = Field(..., alias='name')
    films: List[Optional[PersonFilm]]
