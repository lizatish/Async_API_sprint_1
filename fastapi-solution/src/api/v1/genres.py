from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.genre_service import GenreService, get_genre_service

router = APIRouter()


class Genre(BaseModel):
    """Модель жанра для ответа пользователю."""

    uuid: str
    name: str


@router.get('/{genre_id}', response_model=Genre)
async def genre_details(genre_id: str, genre_service: GenreService = Depends(get_genre_service)) -> Genre:
    """Возвращает подробную информацию о жанре."""
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genre not found')

    return Genre(uuid=genre.id, name=genre.name)


@router.get('/', response_model=List[Genre])
async def genres_list(genre_service: GenreService = Depends(get_genre_service)) -> List[Genre]:
    """Возвращает список жанров."""
    genres_list = await genre_service.get_genres_list()

    result = []
    for genre in genres_list:
        genre_model = Genre(uuid=genre.id, name=genre.name)
        result.append(genre_model)
    return result
