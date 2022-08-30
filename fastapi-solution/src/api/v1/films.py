from typing import List

from fastapi import APIRouter, Depends, Query, Request

from api.v1.errors import FilmNotFound
from api.v1.schemas.films import ShortFilm, Film, Person, Genre
from api.v1.utils import Paginator, get_filter
from services.films import FilmService, get_film_service

router = APIRouter()


@router.get(
    '/',
    response_model=List[ShortFilm],
    summary='Найти фильмы в порядке убывания/возрастания рейтинга,'
            ' удовлетворяющих фильтру',
)
async def films_scope(
        request: Request,
        paginator: Paginator = Depends(),
        film_service: FilmService = Depends(get_film_service),
        filter: dict = Depends(get_filter),
        sort: str = Query(default='-imdb_rating', description='Сортировка'),
) -> List[ShortFilm]:
    """
    Возвращает отсортированный и отфильтрованный список фильмов со следующим содержимым:

    - **uuid**: идентификатор
    - **title**: название
    - **imdb_rating**: рейтинг imdb
    """
    from_ = ((paginator.page_number - 1) * paginator.page_size) if (paginator.page_number > 1) else 0
    films = await film_service.get_scope_films(
        from_=from_, size=paginator.page_size, filter=filter, sort=sort, url=request.url._url,
    )
    if not films:
        raise FilmNotFound()
    return [ShortFilm(
        uuid=item.id,
        title=item.title,
        imdb_rating=item.imdb_rating,
    ) for item in films]


@router.get('/search', response_model=List[ShortFilm], summary='Найти список фильмов по совпадению')
async def film_search(
        request: Request,
        query: str,
        film_service: FilmService = Depends(get_film_service),
        paginator: Paginator = Depends(),
) -> List[ShortFilm]:
    """
    Возвращает список фильмов, удовлетворяющих поиску со следующим содержимым:

    - **uuid**: идентификатор
    - **title**: название
    - **imdb_rating**: рейтинг imdb
    - **description**: описание
    - **genres**: список жанров фильма
    - **actors**: список актеров - участников фильма
    - **writers**: список сценаристов - участников фильма
    - **directors**: список режиссеров - участников фильма
    """
    from_ = ((paginator.page_number - 1) * paginator.page_size) if (paginator.page_number > 1) else 0
    films = await film_service.search_film(
        from_=from_, size=paginator.page_size, query=query, url=request.url._url,
    )
    if not films:
        raise FilmNotFound()
    return [ShortFilm(
        uuid=item.id,
        title=item.title,
        imdb_rating=item.imdb_rating,
    ) for item in films]


@router.get('/{film_id}', response_model=Film, summary='Поиск фильма по идентификатору')
async def film_details(
        film_id: str, film_service: FilmService = Depends(get_film_service),
) -> Film:
    """
    Возвращает фильм со следующим содержимым:

    - **uuid**: идентификатор
    - **title**: название
    - **imdb_rating**: рейтинг imdb
    - **description**: описание
    - **genres**: список жанров фильма
    - **actors**: список актеров - участников фильма
    - **writers**: список сценаристов - участников фильма
    - **directors**: список режиссеров - участников фильма
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
