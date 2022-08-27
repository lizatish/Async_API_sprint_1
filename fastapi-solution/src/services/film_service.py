from functools import lru_cache
from typing import Optional, List

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.main import Film, Person, PersonFilm

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут
PERSON_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class FilmService:
    """Сервис для работы с фильмами."""

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        """Инициализация сервиса."""
        self.redis = redis
        self.elastic = elastic

        self.es_index = 'movies'

    async def get_scope_films(
            self, sort: str = '', filter: str = '', page: int = 20, number: int = 0, query: str = None
    ) -> Optional[Film]:
        films = await self._get_scope_films_from_elastic(page=page, number=number, query=query, sort=sort)
        return films

    async def _get_scope_films_from_elastic(self, page: int = 20, number: int = 0, query: str = None) -> Optional[Film]:
        try:
            if query:
                doc = await self.elastic.search(index="movies", from_=number, size=page, body={
                    "query": {
                        "multi_match": {
                            "query": f"{query}",
                            "fuzziness": "auto"
                        }
                    }
                }, )
            else:
                doc = await self.elastic.search(
                    index='movies',
                    from_=number,
                    size=page,
                    sort='imdb_rating:desc',
                    body={
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "term": {
                                            "genre.id": "3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff"
                                        }
                                    },
                                    {
                                        "term": {
                                            "genre.name": "action"
                                        }
                                    }
                                ]
                            }
                        }
                    }
                )
        except NotFoundError:
            return None
        films = []
        for hit in doc['hits']['hits']:
            films.append(Film(**hit["_source"]))
        return films

    async def get_by_id(self, film_id: str) -> Optional[Film]:
        """Вернуть фильм по идентификатору."""
        film = await self._film_from_cache(film_id)
        if not film:
            film = await self._get_film_from_elastic(film_id)
            if not film:
                return None
            await self._put_film_to_cache(film)

        return film

    async def _get_film_from_elastic(self, film_id: str) -> Optional[Film]:
        try:
            doc = await self.elastic.get(index='movies', id=film_id)
        except NotFoundError:
            return None
        return Film(**doc['_source'])

    async def _film_from_cache(self, film_id: str) -> Optional[Film]:
        data = await self.redis.get(film_id)
        if not data:
            return None

        film = Film.parse_raw(data)
        return film

    async def _person_from_cache(self, person_id: str) -> Optional[Person]:
        data = await self.redis.get(person_id)
        if not data:
            return None
        person = Person.parse_raw(data)
        return person

    async def get_person_by_id(self, person_id: str) -> Optional[Person]:
        """Вернуть фильм по идентификатору."""
        person = await self._person_from_cache(person_id)
        if not person:
            person = await self._get_person_from_elastic(person_id)
        return person

    async def get_films_by_person(self, person_id: str) -> List[Optional[Film]]:
        roles = ['writers', 'actors', 'directors']
        films = []

        for role in roles:
            try:
                docs = await self.elastic.search(
                    index=self.es_index,
                    body={
                        "query": {
                            "nested": {
                                "path": role,
                                "query": {
                                    "bool": {
                                        "must": [
                                            {
                                                "match": {
                                                    f"{role}.id": person_id,
                                                },
                                            },
                                        ],
                                    },
                                },
                            },
                        },
                    },
                )

                for doc in docs['hits']['hits']:
                    source = doc['_source']

                    films.append(Film(**source))

            except NotFoundError:
                pass
        return films

    async def _get_person_from_elastic(self, person_id: str) -> Optional[Person]:
        person = None
        roles = ['writers', 'actors', 'directors']
        try:
            docs = await self.get_film_works_by_person_ids([person_id])

            for doc in docs['hits']['hits']:
                source = doc['_source']
                persons_roles = {}

                for role in roles:
                    person_roles = list(filter(lambda x: x['id'] == person_id, source[role]))
                    if not person_roles:
                        continue

                    person_id, person_name = person_roles[0]['id'], person_roles[0]['name']
                    if role not in persons_roles:
                        persons_roles[role] = {
                            'id': person_id,
                            'full_name': person_name,
                            'fw_ids': [source['id']]
                        }
                    else:
                        persons_roles[role]['fw_ids'].append(source['id'])

                for role, role_data in persons_roles.items():
                    person_film = PersonFilm(role=role[:-1], film_ids=role_data['fw_ids'])
                    if not person:
                        person = Person(
                            id=role_data['id'],
                            full_name=role_data['full_name'],
                            films=[person_film])
                    else:
                        person.films.append(person_film)

        except NotFoundError:
            pass
        return person

    async def _put_film_to_cache(self, film: Film):
        await self.redis.set(film.id, film.json(), expire=FILM_CACHE_EXPIRE_IN_SECONDS)

    async def get_person_by_ids(self, person_ids: List[str]) -> List[Person]:

        persons = []
        roles = ['writers', 'actors', 'directors']

        try:
            docs = await self.get_film_works_by_person_ids(person_ids)

            for person_id in person_ids:
                person = None

                for doc in docs['hits']['hits']:
                    source = doc['_source']
                    persons_roles = {}

                    for role in roles:
                        dirty_person_roles = list(filter(lambda x: x['id'] == person_id, source[role]))
                        person_roles = list({v['id']: v for v in dirty_person_roles}.values())
                        if not person_roles:
                            continue

                        person_id, person_name = person_roles[0]['id'], person_roles[0]['name']
                        if role not in persons_roles:
                            persons_roles[role] = {
                                'id': person_id,
                                'full_name': person_name,
                                'fw_ids': [source['id']]
                            }
                        else:
                            persons_roles[role]['fw_ids'].append(source['id'])

                    for role, role_data in persons_roles.items():
                        person_film = PersonFilm(role=role[:-1], film_ids=role_data['fw_ids'])
                        if not person:
                            person = Person(
                                id=role_data['id'],
                                full_name=role_data['full_name'],
                                films=[person_film])
                        else:
                            person.films.append(person_film)
                persons.append(person)

        except NotFoundError:
            pass
        return persons

    async def get_film_works_by_person_ids(self, person_ids):
        return await self.elastic.search(
            index=self.es_index,
            body={
                "query": {
                    'bool': {
                        'should': [{
                            "nested": {
                                "path": "writers",
                                "query": {
                                    "terms": {
                                        f"writers.id": person_ids
                                    },
                                },
                            }}, {
                            "nested": {
                                "path": "actors",
                                "query": {
                                    "terms": {
                                        f"actors.id": person_ids
                                    },
                                },
                            }}, {
                            "nested": {
                                "path": "directors",
                                "query": {
                                    "terms": {
                                        f"directors.id": person_ids
                                    },
                                },
                            },
                        }]
                    },
                },
            }
        )


@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    """Возвращает экземпляр сервиса для работы с кинопроизведениями."""
    return FilmService(redis, elastic)
