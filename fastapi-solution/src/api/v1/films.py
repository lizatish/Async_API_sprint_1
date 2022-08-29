from typing import List

from fastapi import APIRouter, Depends, Query, Request

from api.v1.errors import FilmNotFound
from api.v1.schemas.films import ShortFilm, Film, Person, Genre
from api.v1.utils import get_page, get_filter
from services.films import FilmService, get_film_service

router = APIRouter()


@router.get('/', response_model=List[ShortFilm], summary='Get and sort all films matching the filter condition')
async def films_scope(
        request: Request,
        page: dict = Depends(get_page),
        film_service: FilmService = Depends(get_film_service),
        filter: dict = Depends(get_filter),
        sort: str = Query(default='-imdb_rating', description='Сортировка'),
) -> List[ShortFilm]:
    """
    Returns all sorted films matching the filter condition with info:

    - **uuid**: film id
    - **title**: film title
    - **imdb_rating**: film imdb rating
    """
    films = await film_service.get_scope_films(
        from_=page['from'], size=page['size'], filter=filter, sort=sort, url=request.url._url,
    )
    if not films:
        raise FilmNotFound()
    return [ShortFilm(
        uuid=item.id,
        title=item.title,
        imdb_rating=item.imdb_rating,
    ) for item in films]


@router.get('/search', response_model=List[ShortFilm], summary='Find a list of films by match')
async def film_search(
        request: Request,
        query: str,
        film_service: FilmService = Depends(get_film_service),
        page: dict = Depends(get_page),
) -> List[ShortFilm]:
    """
     Returns a list of films matching the search terms with info:

    - **uuid**: film id
    - **title**: film title
    - **imdb_rating**: film imdb rating
    - **description**: film description
    - **genres**: all genres of film
    - **actors**: all actors of film
    - **writers**: all writers of film
    - **directors**: all directors of film
    """
    films = await film_service.search_film(
        from_=page['from'], size=page['size'], query=query, url=request.url._url,
    )
    if not films:
        raise FilmNotFound()
    return [ShortFilm(
        uuid=item.id,
        title=item.title,
        imdb_rating=item.imdb_rating,
    ) for item in films]


@router.get('/{film_id}', response_model=Film, summary='Find film by id')
async def film_details(
        film_id: str , film_service: FilmService = Depends(get_film_service),
) -> Film:
    """
    Return a film with all the information:

    - **uuid**: film id
    - **title**: film title
    - **imdb_rating**: film imdb rating
    - **description**: film description
    - **genres**: all genres of film
    - **actors**: all actors of film
    - **writers**: all writers of film
    - **directors**: all directors of film
    """
    film = await film_service.get_by_id(film_id)
    if not film:
        raise FilmNotFound()
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
