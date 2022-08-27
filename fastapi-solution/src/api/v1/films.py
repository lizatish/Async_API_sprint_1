from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from api.v1.schemas import ShortFilm, Film, Person, Genre
from api.v1.utils import get_page, get_filter
from services.films import FilmService, get_film_service

router = APIRouter()


@router.get('/', response_model=List[ShortFilm])
async def films_scope(
        request: Request,
        page: dict = Depends(get_page),
        film_service: FilmService = Depends(get_film_service),
        filter: dict = Depends(get_filter),
        sort: str = Query(default='-imdb_rating'),
) -> List[ShortFilm]:
    """Возвращает списка фильмов в соответствии с фильтрами."""
    films = await film_service.get_scope_films(
        from_=page['from'], size=page['size'], filter=filter, sort=sort, url=request.url._url,
    )
    if not films:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='film not found',
        )
    return [ShortFilm(
        uuid=item.id,
        title=item.title,
        imdb_rating=item.imdb_rating,
    ) for item in films]


@router.get('/search', response_model=List[ShortFilm])
async def film_search(
        request: Request,
        query: str,
        film_service: FilmService = Depends(get_film_service),
        page: dict = Depends(get_page),
) -> List[ShortFilm]:
    """Возвращает результат поиска фильма."""
    films = await film_service.search_film(
        from_=page['from'], size=page['size'], query=query, url=request.url._url,
    )
    if not films:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='film not found',
        )
    return [ShortFilm(
        uuid=item.id,
        title=item.title,
        imdb_rating=item.imdb_rating,
    ) for item in films]


@router.get('/{film_id}', response_model=Film)
async def film_details(
        film_id: str, film_service: FilmService = Depends(get_film_service),
) -> Film:
    """Ищет фильм по id."""
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='film not found',
        )
    result = Film(
        uuid=film.id,
        title=film.title,
        imdb_rating=film.imdb_rating,
        description=film.description,
        genres=[Genre(uuid=genre.id, name=genre.name) for genre in film.genres],
        actors=[Person(uuid=person.id, full_name=person.full_name) for person in film.actors],
        writers=[Person(uuid=person.id, full_name=person.full_name) for person in film.writers],
        directors=[Person(uuid=person.id, full_name=person.full_name) for person in film.directors],
    )
    return result
