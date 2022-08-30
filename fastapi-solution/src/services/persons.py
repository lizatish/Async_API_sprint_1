from functools import lru_cache
from typing import Optional, List

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from core.config import get_settings
from db.elastic import get_elastic
from db.redis import get_redis
from models.main import Person

conf = get_settings()


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

    async def search_person(self, query: str, from_: int, size: int, url: str) -> Optional[List[Person]]:
        """Возвращает совпадения по персоне."""
        persons = await self._persons_from_cache(url)
        if not persons:
            persons = await self._search_person_from_elastic(query=query, from_=from_, size=size)
            if not persons:
                return None
            await self._put_persons_to_cache(persons, url)
        return persons

    async def _search_person_from_elastic(self, query: str, from_: int, size: int) -> Optional[List[Person]]:
        """Ищет данные по персоне в индексе персон."""
        try:
            doc = await self.elastic.search(
                index=self.es_index,
                from_=from_,
                size=size,
                body={
                    'query': {
                        'multi_match': {
                            'query': f'{query}',
                            'fuzziness': 'auto',
                        },
                    },
                },
            )
        except NotFoundError:
            return None
        return [Person(**hit['_source']) for hit in doc['hits']['hits']]

    async def enrich_person_data(self, main_person_info: Person, fw_person_info: Person) -> Person:
        """Обогащает данные по персоне, возвращает полные данные по персоне."""
        person = await self._enriched_person_from_cache(main_person_info.id)
        if not person:
            person = main_person_info.copy()
            person.films = fw_person_info.films.copy()
            await self._put_enriched_person_to_cache(person)
        return person

    async def _enriched_person_from_cache(self, person_id: str) -> Optional[Person]:
        """Получает персону из кеша редиса."""
        data = await self.redis.get(f'enriched_{person_id}')
        if not data:
            return None
        person = Person.parse_raw(data)
        return person

    async def _put_enriched_person_to_cache(self, person: Person):
        """Кладет персону в кеш редиса."""
        await self.redis.set(f'enriched_{person.id}', person.json(), expire=conf.PERSON_CACHE_EXPIRE_IN_SECONDS)

    async def _person_from_cache(self, person_id: str) -> Optional[Person]:
        """Кладет персону в кеш редиса."""
        data = await self.redis.get(person_id)
        if not data:
            return None
        person = Person.parse_raw(data)
        return person

    async def _put_person_to_cache(self, person: Person):
        """Получает персону из кеша редиса."""
        await self.redis.set(person.id, person.json(), expire=conf.PERSON_CACHE_EXPIRE_IN_SECONDS)

    async def _get_person_from_elastic(self, person_id: str) -> Optional[Person]:
        """Возвращает персону из эластика."""
        person = None
        try:
            docs = await self.elastic.search(
                index=self.es_index,
                body={
                    'query': {
                        'bool': {
                            'must': [
                                {
                                    'match_phrase': {
                                        'id': person_id,
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

    async def enrich_persons_list_data(self, persons: List[Person], fw_person_info: List[Person]) -> List[Person]:
        """Возвращает полный список персон с расширенными данными."""
        full_persons = []
        for person_base, person_fw in zip(persons, fw_person_info):
            if person_fw:
                full_person = await self.enrich_person_data(person_base, person_fw)
            else:
                full_person = person_base
            full_persons.append(full_person)
        return full_persons

    async def _persons_from_cache(self, url: str):
        """Функция отдаёт список персон если они есть в кэше."""
        data = await self.redis.lrange(url, 0, -1)
        if not data:
            return None
        persons = [Person.parse_raw(item) for item in data]
        return list(reversed(persons))

    async def _put_persons_to_cache(self, persons: List[Person], url: str):
        """Функция кладёт список персон в кэш."""
        data = [item.json() for item in persons]
        await self.redis.lpush(
            url, *data,
        )
        await self.redis.expire(url, conf.PERSON_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    """Возвращает экземпляр сервиса для работы с участниками фильма."""
    return PersonService(redis, elastic)
