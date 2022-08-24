from http import HTTPStatus
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.film_service import FilmService, get_film_service
from services.person_service import PersonService, get_person_service

router = APIRouter()


class PersonFilm(BaseModel):
    role: Literal['actor', 'writer', 'director']
    film_ids: List[str]


class Person(BaseModel):
    """Модель фильма для ответа пользователю."""

    uuid: str
    films: List[Optional[PersonFilm]] = []


@router.get('/{person_id}', response_model=Person)
async def person_details(person_id: str, person_service: PersonService = Depends(get_person_service),
                         film_service: FilmService = Depends(get_film_service)) -> Person:
    """Возвращает подробную информацию об участнике фильма."""

    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    fw_person_info = await film_service.get_person_by_id(person_id)
    person = await person_service.enrich_person_data(person, fw_person_info)

    return Person(uuid=person.id, films=person.films)
