from functools import lru_cache
from typing import Optional

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.film import Film

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class FilmService:
    """Сервис для работы с фильмами."""

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        """Инициализация сервиса."""
        self.redis = redis
        self.elastic = elastic


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
                },)
            else:
                doc = await self.elastic.search(
                    index='movies',
                    from_=number,
                    size=page,
                    sort='imdb_rating:desc',
                    body= {
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
        # Пытаемся получить данные о фильме из кеша, используя команду get
        # https://redis.io/commands/get
        data = await self.redis.get(film_id)
        if not data:
            return None

        # pydantic предоставляет удобное API для создания объекта моделей из json
        film = Film.parse_raw(data)
        return film

    async def _put_film_to_cache(self, film: Film):
        # Сохраняем данные о фильме, используя команду set
        # Выставляем время жизни кеша — 5 минут
        # https://redis.io/commands/set
        # pydantic позволяет сериализовать модель в json
        await self.redis.set(film.id, film.json(), expire=FILM_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    """Возвращает экземпляр сервиса для работы с кинопроизведениями."""
    return FilmService(redis, elastic)
