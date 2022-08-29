import datetime
from typing import Optional

from pydantic.dataclasses import dataclass

from common.models.main import FilmWorkId, PersonId, GenreId


@dataclass(frozen=True)
class EnrichResult:
    """Модель результата выполнения запроса по обогащению данных."""

    id: str
    updated_at: datetime.datetime


@dataclass(frozen=True)
class MergeResult:
    """Модель результата выполнения запроса по склейке данных."""

    film_work_id: FilmWorkId
    film_work_title: str
    film_work_description: Optional[str]
    film_work_rating: Optional[float]
    film_work_type: str
    film_work_created_at: datetime.datetime
    film_work_updated_at: datetime.datetime
    pfw_role: Optional[str]
    person_id: Optional[PersonId]
    person_full_name: Optional[str]
    genre_name: str
    genre_id: GenreId
