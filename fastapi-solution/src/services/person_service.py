from functools import lru_cache
from typing import Optional

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.person import Person, PersonFilm

PERSON_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class PersonService:
    """Сервис для работы с участниками фильма."""

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        """Инициализация сервиса."""
        self.redis = redis
        self.elastic = elastic

        self.es_index = 'persons'

    async def get_by_id(self, person_id: str) -> Optional[Person]:
        """Возвращает участника фильма по идентификатору."""
        person = await self._person_from_cache(person_id)
        if not person:
            person = await self._get_person_from_elastic(person_id)
            if not person:
                return None
            await self._put_person_to_cache(person)

        return person

    async def _get_person_from_elastic(self, person_id: str) -> Optional[Person]:

        person = None
        # todo добавить directors
        roles = ['writers', 'actors']
        for role in roles:
            try:
                docs = await self.elastic.search(
                    index='movies',
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

                persons_roles = {}
                for doc in docs['hits']['hits']:
                    source = doc['_source']

                    person_roles = list(filter(lambda x: x['id'] == person_id, source[role]))
                    if not person_roles:
                        # todo
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

    async def _person_from_cache(self, person_id: str) -> Optional[Person]:
        data = await self.redis.get(person_id)
        if not data:
            return None
        person = Person.parse_raw(data)
        return person

    async def _put_person_to_cache(self, person: Person):
        await self.redis.set(person.id, person.json(), expire=PERSON_CACHE_EXPIRE_IN_SECONDS)

    # async def get_scope_films(
    #         self, sort: str = '', filter: str = '', page: int = 20, number: int = 0, query: str = None
    # ) -> Optional[Film]:
    #     films = await self._get_scope_films_from_elastic(page=page, number=number, query=query, sort=sort)
    #     return films
    #
    # async def _get_scope_films_from_elastic(self, page: int = 20, number: int = 0, query: str = None) -> Optional[Film]:
    #     try:
    #         if query:
    #             doc = await self.elastic.search(index="movies", from_=number, size=page, body={
    #                 "query": {
    #                     "multi_match": {
    #                         "query": f"{query}",
    #                         "fuzziness": "auto"
    #                     }
    #                 }
    #             }, )
    #         else:
    #             doc = await self.elastic.search(
    #                 index='movies',
    #                 from_=number,
    #                 size=page,
    #                 sort='imdb_rating:desc',
    #                 body={
    #                     "query": {
    #                         "bool": {
    #                             "must": [
    #                                 {
    #                                     "term": {
    #                                         "genre.id": "3d8d9bf5-0d90-4353-88ba-4ccc5d2c07ff"
    #                                     }
    #                                 },
    #                                 {
    #                                     "term": {
    #                                         "genre.name": "action"
    #                                     }
    #                                 }
    #                             ]
    #                         }
    #                     }
    #                 }
    #             )
    #     except NotFoundError:
    #         return None
    #     films = []
    #     for hit in doc['hits']['hits']:
    #         films.append(Person(**hit["_source"]))
    #     return films


@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    """Возвращает экземпляр сервиса для работы с участниками фильма."""
    return PersonService(redis, elastic)
