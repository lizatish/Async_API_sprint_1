from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from schemas.schemas import Film, ShortFilm
from services.film import FilmService, get_film_service
from .utils import get_filter, get_page

router = APIRouter()


@router.get("/")
async def films_scope(
        page: dict = Depends(get_page),
        film_service: FilmService = Depends(get_film_service),
        filter: dict = Depends(get_filter),
        sort: str = Query(default='-imdb_rating'),
) -> List[ShortFilm]:
    """API для получения списка фильмов в соответствии с фильтрами."""
    films = await film_service.get_scope_films(
        from_=page['from'], size=page['size'], filter=filter, sort=sort
    )
    if not films:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='film not found'
        )
    return [ShortFilm(
        uuid=item.uuid,
        title=item.title,
        imdb_rating=item.imdb_rating
    ) for item in films]


@router.get("/search")
async def film_search(
        query: str,
        film_service: FilmService = Depends(get_film_service),
        page: dict = Depends(get_page),
) -> List[Film]:
    """API для поиска фильма."""
    films = await film_service.search_film(
        from_=page['from'], size=page['size'], query=query
    )
    if not films:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='film not found'
        )
    return [ShortFilm(
        uuid=item.uuid,
        title=item.title,
        imdb_rating=item.imdb_rating
    ) for item in films]


@router.get('/{film_id}', response_model=Film)
async def film_details(
        film_id: str, film_service: FilmService = Depends(get_film_service)
) -> Film:
    """API для поиска фильма по id."""
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='film not found'
        )
    result = Film(
        uuid=film.uuid,
        title=film.title,
        imdb_rating=film.imdb_rating,
        description=film.description,
        genre=film.genre,
        actors=film.actors,
        writers=film.writers,
        directors=film.directors
    )
    return result
