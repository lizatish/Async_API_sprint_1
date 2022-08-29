from typing import List

from fastapi import APIRouter, Depends, Request

from api.v1.errors import GenreNotFound
from api.v1.schemas.genres import Genre
from services.genres import GenreService, get_genre_service

router = APIRouter()


@router.get('/{genre_id}', response_model=Genre, summary='Get genre by id')
async def genre_details(
        genre_id: str,
        genre_service: GenreService = Depends(get_genre_service),
) -> Genre:
    """
    Return a genre by id with all the information:

    - **uuid**: genre id
    - **name**: genre name
    """
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise GenreNotFound()

    return Genre(uuid=genre.id, name=genre.name)


@router.get('/', response_model=List[Genre], summary='Get list of all genres')
async def genres_list(
        request: Request,
        genre_service: GenreService = Depends(get_genre_service),
) -> List[Genre]:
    """
    Return a list of genres with all the information:

    - **uuid**: genre id
    - **name**: genre name
    """
    genres = await genre_service.get_genres_list(url=request.url._url)

    if not genres:
        raise GenreNotFound()

    result = []
    for genre in genres:
        genre_model = Genre(uuid=genre.id, name=genre.name)
        result.append(genre_model)
    return result
