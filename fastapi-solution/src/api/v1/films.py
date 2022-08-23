import re
from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Query, Request

from schemas.schemas import Film, ShortFilm
from services.film_service import FilmService, get_film_service

router = APIRouter()


def get_page(req: Request) -> dict:
    number = req.query_params.get('page[number]')
    size = req.query_params.get('page[size]')
    if number and size:
        from_ = (int(number) - 1) * int(size)
    else:
        from_ = 0
    return {
        "size": int(size) if size else 5,
        "from": from_
    }


def get_filter(req: Request) -> dict:
    filter_ = {}
    for key, value in req.query_params.items():
        if re.match('^filter\[[a-zA-Z]{0,25}\]$', key) is not None:
            filter_[key.replace('filter[', '').replace(']', '')] = value
    return filter_


@router.get("/")
async def films_scope(
        page: dict = Depends(get_page),
        film_service: FilmService = Depends(get_film_service),
        filter: dict = Depends(get_filter),
        sort: str = Query(default=None),
) -> List[ShortFilm]:
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
