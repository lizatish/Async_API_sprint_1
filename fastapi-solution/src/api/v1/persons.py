from http import HTTPStatus
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.v1.utils import get_page
from services.films import FilmService, get_film_service
from services.persons import PersonService, get_person_service

router = APIRouter()


class PersonFilm(BaseModel):
    """Вложенная модель для описания фильмов по персоне."""

    role: Literal['actor', 'writer', 'director']
    film_ids: List[str]


class Person(BaseModel):
    """Модель фильма для ответа пользователю."""

    uuid: str
    full_name: str
    films: List[Optional[PersonFilm]] = []


class FilmByPerson(BaseModel):
    """Модель для представления получения фильмов по персоне."""

    uuid: str
    title: str
    imdb_rating: float


@router.get('/{person_id}/film', response_model=List[FilmByPerson])
async def films_by_person(person_id: str,
                          film_service: FilmService = Depends(get_film_service)) -> List[FilmByPerson]:
    """Ищет фильмы по персоне."""
    fws_by_person = await film_service.get_films_by_person(person_id)
    if not fws_by_person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    result = []
    for fw in fws_by_person:
        fw_model = FilmByPerson(
            uuid=fw.id,
            title=fw.title,
            imdb_rating=fw.imdb_rating,
        )
        result.append(fw_model)
    return result


@router.get('/search', response_model=List[Person])
async def search_persons(
        query: str,
        person_service: PersonService = Depends(get_person_service),
        film_service: FilmService = Depends(get_film_service),
        page: dict = Depends(get_page),
) -> List[Person]:
    """Ищет совпадения по персонам."""
    persons = await person_service.search_person(
        from_=page['from'], size=page['size'], query=query,
    )
    if not persons:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='film not found',
        )

    person_ids = [person.id for person in persons]
    fw_person_info = await film_service.get_person_by_ids(person_ids)
    full_persons = await person_service.enrich_persons_list_data(persons, fw_person_info)

    result = []
    for person in full_persons:
        result.append(
            Person(
                uuid=person.id,
                full_name=person.full_name,
                films=person.films,
            ))

    return result


@router.get('/{person_id}', response_model=Person)
async def person_details(person_id: str, person_service: PersonService = Depends(get_person_service),
                         film_service: FilmService = Depends(get_film_service)) -> Person:
    """Возвращает подробную информацию об участнике фильма."""
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    fw_person_info = await film_service.get_person_by_id(person_id)
    person = await person_service.enrich_person_data(person, fw_person_info)

    return Person(uuid=person.id, full_name=person.full_name, films=person.films)
