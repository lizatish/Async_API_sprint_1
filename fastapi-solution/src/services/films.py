from functools import lru_cache
from typing import Optional, List

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from core.config import get_settings
from db.elastic import get_elastic
from db.redis import get_redis
from models.common import FilterSimpleValues, FilterNestedValues
from models.main import Film, Person, PersonFilm

conf = get_settings()


class FilmService:
    """Сервис для работы с фильмами."""

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        """Инициализация сервиса."""
        self.redis = redis
        self.elastic = elastic

        self.es_index = 'movies'
        self.person_roles = ['writers', 'actors', 'directors']

    async def get_by_id(self, film_id: str) -> Optional[Film]:
        """Функция для получения фильма по id."""
        film = await self._film_from_cache(film_id)
        if not film:
            film = await self._get_film_from_elastic(film_id)
            if not film:
                return None
            await self._put_film_to_cache(film)
        return film

    async def get_scope_films(
            self, from_: int, size: int, filter: dict, sort: str, url: str,
    ) -> Optional[List[Film]]:
        """Функция для получения списка фильмов."""
        films = await self._films_from_cache(url)
        if not films:
            films = await self._get_scope_films_from_elastic(
                from_=from_, size=size, sort=sort, filter_=filter,
            )
            if not films:
                return None
            await self._put_films_to_cache(films, url)
        return films

    async def search_film(
            self, query: str, from_: int, size: int, url: str,
    ) -> Optional[List[Film]]:
        """Функция для поиска фильма."""
        films = await self._films_from_cache(url)
        if not films:
            films = await self._search_film_from_elastic(
                query=query, from_=from_, size=size,
            )
            if not films:
                return None
            await self._put_films_to_cache(films, url)
        return films

    async def get_films_by_person(self, person_id: str) -> List[Optional[Film]]:
        """Возвращает фильмы, в которых участвовала персона."""
        films = await self._films_from_cache(f'film_by_person_{person_id}')
        if not films:
            films = []
            try:
                docs = await self._get_by_person_ids_from_elastic([person_id])
                for doc in docs['hits']['hits']:
                    source = doc['_source']
                    films.append(Film(**source))
                await self._put_films_to_cache(films, f'film_by_person_{person_id}')
            except NotFoundError:
                pass
        return films

    async def get_person_by_id(self, person_id: str) -> Optional[Person]:
        """Возвращает персону по идентификатору."""
        person = await self._person_from_cache(f'info_{person_id}')
        if not person:
            person = await self._get_person_from_elastic(person_id)
            if not person:
                return None
            await self._put_person_to_cache(person)
        return person

    async def get_person_by_ids(self, person_ids: List[str]) -> List[Person]:
        """Возвращает набор персон по списку идентификаторов."""
        persons = await self._persons_from_cache('-'.join(person_ids))
        if not persons:
            persons = []
            try:
                docs = await self._get_by_person_ids_from_elastic(person_ids)
                for person_id in person_ids:
                    person = await self._prepare_person(person_id, docs)
                    persons.append(person)
                await self._put_persons_to_cache(persons, '-'.join(person_ids))
            except NotFoundError:
                pass
        return persons

    async def _get_person_from_elastic(self, person_id: str) -> Optional[Optional[Person]]:
        """Возвращает персону из эластика."""
        person = None
        try:
            docs = await self._get_by_person_ids_from_elastic([person_id])
            person = await self._prepare_person(person_id, docs)
        except NotFoundError:
            pass
        return person

    async def _search_film_from_elastic(
            self, query: str, from_: int, size: int,
    ) -> Optional[List[Film]]:
        """Функция для поиска фильма в elasticsearch."""
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
        return [Film(**hit['_source']) for hit in doc['hits']['hits']]

    async def _get_scope_films_from_elastic(
            self, from_: int, size: int, filter_: dict, sort: str,
    ) -> Optional[List[Film]]:
        """Функция для поиска фильмов в elasticsearch в соот. фильтрам."""
        try:
            if filter_:

                filter_nested_values = FilterNestedValues.get_values()
                filter_simple_values = FilterSimpleValues.get_values()
                body = []
                for key in filter_:
                    if key in filter_nested_values:
                        body.append(
                            {
                                'nested': {
                                    'path': f'{key}',
                                    'query': {
                                        'bool': {
                                            'must': [
                                                {
                                                    'match': {
                                                        f'{key}.id': f'{filter_[key]}',
                                                    },
                                                },
                                            ],
                                        },
                                    },
                                },
                            },
                        )
                    elif key in filter_simple_values:
                        body.append({'match': {f'{key}': f'{filter_[key]}'}})

                doc = await self.elastic.search(
                    index=self.es_index,
                    from_=from_,
                    size=size,
                    sort=f'{sort[1:]}:desc' if sort[0] == '-'
                    else f'{sort}:asc',
                    body={
                        'query': {'bool': {'must': body}},
                    },
                )
            else:
                doc = await self.elastic.search(
                    index=self.es_index,
                    from_=from_,
                    size=size,
                    sort=f'{sort[1:]}:desc' if sort[0] == '-'
                    else f'{sort}:asc',
                )
        except NotFoundError:
            return None
        return [Film(**hit['_source']) for hit in doc['hits']['hits']]

    async def _get_film_from_elastic(self, film_id: str) -> Optional[Film]:
        """Функция для поиска фильма в elasticsearch по id."""
        try:
            doc = await self.elastic.get(index=self.es_index, id=film_id)
        except NotFoundError:
            return None
        return Film(**doc['_source'])

    async def _film_from_cache(self, film_id: str) -> Optional[Film]:
        """Функция отдаёт фильм по id если он есть в кэше."""
        data = await self.redis.get(film_id)
        if not data:
            return None
        film = Film.parse_raw(data)
        return film

    async def _put_film_to_cache(self, film: Film):
        """Функция кладёт фильм по id в кэш."""
        await self.redis.set(
            film.id, film.json(), expire=conf.FILM_CACHE_EXPIRE_IN_SECONDS,
        )

    async def _person_from_cache(self, person_id: str) -> Optional[Person]:
        """Возвращает персону ид кеша редиса."""
        data = await self.redis.get(person_id)
        if not data:
            return None
        person = Person.parse_raw(data)
        return person

    async def _prepare_person(self, person_id: str, docs: dict) -> Person:
        """Подготавливает полные данные по персоне и возвращает их."""
        person = None
        persons_roles = {}
        for doc in docs['hits']['hits']:
            source = doc['_source']

            for role in self.person_roles:
                dirty_person_roles = list(filter(lambda x: x['id'] == person_id, source[role]))
                person_roles = list({v['id']: v for v in dirty_person_roles}.values())
                if not person_roles:
                    continue

                person_id, person_name = person_roles[0]['id'], person_roles[0]['name']
                if role not in persons_roles:
                    persons_roles[role] = {
                        'id': person_id,
                        'full_name': person_name,
                        'fw_ids': [source['id']],
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

        return person

    async def _get_by_person_ids_from_elastic(self, person_ids: List[str]) -> dict:
        """Возвращает результат запроса к elastic для поиска персон."""
        return await self.elastic.search(
            index=self.es_index,
            body={
                'query': {
                    'bool': {
                        'should': [
                            {
                                'nested': {
                                    'path': 'writers',
                                    'query': {
                                        'terms': {
                                            'writers.id': person_ids,
                                        },
                                    },
                                },
                            },
                            {
                                'nested': {
                                    'path': 'actors',
                                    'query': {
                                        'terms': {
                                            'actors.id': person_ids,
                                        },
                                    },
                                },
                            },
                            {
                                'nested': {
                                    'path': 'directors',
                                    'query': {
                                        'terms': {
                                            'directors.id': person_ids,
                                        },
                                    },
                                },
                            },
                        ],
                    },
                },
            },
        )

    async def _films_from_cache(self, url: str):
        """Функция отдаёт список фильмов если они есть в кэше."""
        data = await self.redis.lrange(url, 0, -1)
        if not data:
            return None
        films = [Film.parse_raw(item) for item in data]
        return reversed(films)

    async def _put_films_to_cache(self, films: List[Film], url: str):
        """Функция кладёт список фильмов в кэш."""
        data = [item.json() for item in films]
        await self.redis.lpush(
            url, *data,
        )
        await self.redis.expire(url, conf.FILM_CACHE_EXPIRE_IN_SECONDS)

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

    async def _put_person_to_cache(self, person: Person):
        """Получает персону из кеша редиса."""
        await self.redis.set(f'info_{person.id}', person.json(), expire=conf.PERSON_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    """Возвращает экземпляр сервиса для работы с кинопроизведениями."""
    return FilmService(redis, elastic)
