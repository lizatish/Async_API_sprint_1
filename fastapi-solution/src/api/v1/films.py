from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.film import FilmService, get_film_service

router = APIRouter()


class Film(BaseModel):
    """Модель фильма для ответа пользователю."""

    uuid: UUID
    title: str


@router.get('/{film_id}', response_model=Film)
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> Film:
    """Возвращает подробную информацию о фильме."""
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

    return Film(uuid=film.uuid, title=film.title)
