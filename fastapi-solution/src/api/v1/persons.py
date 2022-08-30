from typing import List

from fastapi import APIRouter, Depends, Request, Query

from api.v1.errors import PersonNotFound
from api.v1.schemas.persons import FilmByPerson, Person
from api.v1.utils import Paginator
from services.films import FilmService, get_film_service
from services.persons import PersonService, get_person_service

router = APIRouter()


@router.get(
    '/{person_id}/film',
    response_model=List[FilmByPerson],
    summary='Найти фильмы по идентификатору участника',
)
async def films_by_person(
        person_id: str,
        film_service: FilmService = Depends(get_film_service),
) -> List[FilmByPerson]:
    """
    Возвращает список фильмов, где участвовал персонаж со следующим содержимым:

    - **uuid**: идентификатор
    - **full_name**: полное имя
    - **films**: фильмы, где участвовал
    """
    fws_by_person = await film_service.get_films_by_person(person_id)
    if not fws_by_person:
        raise PersonNotFound()

    return [
        FilmByPerson(
            uuid=fw.id,
            title=fw.title,
            imdb_rating=fw.imdb_rating,
        ) for fw in fws_by_person
    ]


@router.get('/search', response_model=List[Person], summary='Найти участников фильма')
async def search_persons(
        request: Request,
        query: str = Query(..., description='Поисковой запрос'),
        paginator: Paginator = Depends(),
        person_service: PersonService = Depends(get_person_service),
        film_service: FilmService = Depends(get_film_service),
) -> List[Person]:
    """
    Возвращает список всех персон, удовлетворяющих условиям поиска со следующим содержимым:

    - **uuid**: идентификатор
    - **full_name**: полное имя
    - **films**: фильмы, где участвовал
    """
    from_ = ((paginator.page_number - 1) * paginator.page_size) if (paginator.page_number > 1) else 0
    persons = await person_service.search_person(
        from_=from_, size=paginator.page_size, query=query, url=request.url._url,
    )
    if not persons:
        raise PersonNotFound()

    person_ids = [person.id for person in persons]
    fw_person_info = await film_service.get_person_by_ids(person_ids)
    full_persons = await person_service.enrich_persons_list_data(persons, fw_person_info)

    return [
        Person(
            uuid=person.id,
            full_name=person.full_name,
            films=person.films,
        ) for person in full_persons
    ]


@router.get('/{person_id}', response_model=Person, summary='Найти участника фильма по идентификатору')
async def person_details(
        person_id: str,
        person_service: PersonService = Depends(get_person_service),
        film_service: FilmService = Depends(get_film_service),
) -> Person:
    """
    Возвращает подробную информацию об участнике фильма со следующим содержимым:

    - **uuid**: идентификатор
    - **full_name**: полное имя
    - **films**: фильмы, где участвовал
    """
    person = await person_service.get_by_id(person_id)
    if not person:
        raise PersonNotFound()
    fw_person_info = await film_service.get_person_by_id(person_id)
    person = await person_service.enrich_person_data(person, fw_person_info)
    return Person(uuid=person.id, full_name=person.full_name, films=person.films)
