from functools import lru_cache
from typing import Optional, List

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from core.config import get_settings
from db.elastic import get_elastic
from db.redis import get_redis
from models.main import Genre

conf = get_settings()


class GenreService:
    """Сервис для работы с жанрами."""

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        """Инициализация сервиса."""
        self.redis = redis
        self.elastic = elastic

        self.es_index = 'genres'

    async def get_genres_list(self, url: str) -> List[Genre]:
        """Возвращает список всех жанров."""
        genres = await self._genres_from_cache(url)
        if not genres:
            genres = []
            try:
                docs = await self.elastic.search(
                    index=self.es_index,
                    body={
                        'size': 10000,
                        'query': {
                            'match_all': {},
                        },
                    },
                )
                genre_docs = docs['hits']['hits']
                for genre_doc in genre_docs:
                    genres.append(Genre(**genre_doc['_source']))
                await self._put_genres_to_cache(genres, url)
            except NotFoundError:
                pass

        return genres

    async def get_by_id(self, genre_id: str) -> Optional[Genre]:
        """Возвращает жанр по идентификатору."""
        genre = await self._genre_from_cache(genre_id)
        if not genre:
            genre = await self._get_genre_from_elastic(genre_id)
            if not genre:
                return None
            await self._put_genre_to_cache(genre)

        return genre

    async def _get_genre_from_elastic(self, genre_id: str) -> Optional[Genre]:
        """Получает жанр из elastic."""
        genre = None
        try:
            docs = await self.elastic.search(
                index=self.es_index,
                body={
                    'query': {
                        'bool': {
                            'must': [
                                {
                                    'match_phrase': {
                                        'id': genre_id,
                                    },
                                },
                            ],
                        },
                    },
                },
            )
            doc = docs['hits']['hits']
            if doc:
                genre = Genre(**doc[0]['_source'])
        except NotFoundError:
            pass

        return genre

    async def _genre_from_cache(self, genre_id: str) -> Optional[Genre]:
        data = await self.redis.get(genre_id)
        if not data:
            return None

        genre = Genre.parse_raw(data)
        return genre

    async def _put_genre_to_cache(self, genre: Genre):
        await self.redis.set(genre.id, genre.json(), expire=conf.GENRE_CACHE_EXPIRE_IN_SECONDS)

    async def _genres_from_cache(self, url: str):
        """Функция отдаёт список жанров если они есть в кэше."""
        data = await self.redis.lrange(url, 0, -1)
        if not data:
            return None
        genres = [Genre.parse_raw(item) for item in data]
        return reversed(genres)

    async def _put_genres_to_cache(self, genres: List[Genre], url: str):
        """Функция кладёт список жанров в кэш."""
        data = [item.json() for item in genres]
        await self.redis.lpush(
            url, *data,
        )
        await self.redis.expire(url, conf.GENRE_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_genre_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    """Возвращает экземпляр сервиса для работы с жанрами."""
    return GenreService(redis, elastic)
