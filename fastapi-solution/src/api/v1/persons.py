from typing import List

from fastapi import APIRouter, Depends, Request, Query

from api.v1.errors import PersonNotFound
from api.v1.schemas.persons import FilmByPerson, Person
from api.v1.utils import get_page
from services.films import FilmService, get_film_service
from services.persons import PersonService, get_person_service

router = APIRouter()


@router.get('/{person_id}/film', response_model=List[FilmByPerson], summary='Get films with person member')
async def films_by_person(
        person_id: str,
        film_service: FilmService = Depends(get_film_service),
) -> List[FilmByPerson]:
    """
    Return list of films, where a person was a member with info:

    - **uuid**: film id
    - **title**: film title
    - **imdb_rating**: film imdb rating
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


@router.get('/search', response_model=List[Person], summary='Search persons')
async def search_persons(
        request: Request,
        query: str = Query(..., description="Search query"),
        page: dict = Depends(get_page),
        person_service: PersonService = Depends(get_person_service),
        film_service: FilmService = Depends(get_film_service),
) -> List[Person]:
    """
    Return list of all persons matching the search terms with info:

    - **uuid**: person id
    - **full_name**: person full name
    - **films**: films where the person was a member
    """
    persons = await person_service.search_person(
        from_=page['from'], size=page['size'], query=query, url=request.url._url,
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


@router.get('/{person_id}', response_model=Person, summary='Get person by id')
async def person_details(
        person_id: str,
        person_service: PersonService = Depends(get_person_service),
        film_service: FilmService = Depends(get_film_service),
) -> Person:
    """
    Return a genre by id with all the information:

    - **uuid**: person id
    - **full_name**: person full name
    - **films**: films where the person was a member
    """
    person = await person_service.get_by_id(person_id)
    if not person:
        raise PersonNotFound()
    fw_person_info = await film_service.get_person_by_id(person_id)
    person = await person_service.enrich_person_data(person, fw_person_info)
    return Person(uuid=person.id, full_name=person.full_name, films=person.films)
