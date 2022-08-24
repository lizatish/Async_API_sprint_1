from functools import lru_cache
from typing import Optional

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.person import Person

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
        return person

    async def enrich_person_data(self, main_person_info: Person, fw_person_info: Person):
        person = main_person_info.copy()
        person.films = fw_person_info.films.copy()
        await self._put_person_to_cache(person)
        return person

    async def _person_from_cache(self, person_id: str) -> Optional[Person]:
        data = await self.redis.get(person_id)
        if not data:
            return None
        person = Person.parse_raw(data)
        return person

    async def _put_person_to_cache(self, person: Person):
        await self.redis.set(person.id, person.json(), expire=PERSON_CACHE_EXPIRE_IN_SECONDS)

    async def _get_person_from_elastic(self, person_id: str) -> Optional[Person]:
        person = None
        try:
            docs = await self.elastic.search(
                index=self.es_index,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "match_phrase": {
                                        "id": person_id,
                                    },
                                },
                            ],
                        },
                    },
                },
            )
            doc = docs['hits']['hits']
            if doc:
                person = Person(**doc[0]['_source'])
        except NotFoundError:
            pass

        return person


@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    """Возвращает экземпляр сервиса для работы с участниками фильма."""
    return PersonService(redis, elastic)
