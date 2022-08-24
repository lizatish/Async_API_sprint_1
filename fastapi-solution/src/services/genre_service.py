from functools import lru_cache
from typing import Optional

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.main import Genre

GENRE_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class GenreService:
    """Сервис для работы с жанрами."""

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        """Инициализация сервиса."""
        self.redis = redis
        self.elastic = elastic

        self.es_index = 'genres'

    async def get_scope_genres(
            self, sort: str = '', filter: str = '', page: int = 20, number: int = 0, query: str = None
    ) -> Optional[Genre]:
        genres = await self._get_scope_genres_from_elastic(page=page, number=number, query=query, sort=sort)
        return genres

    async def _get_scope_genres_from_elastic(self, page: int = 20, number: int = 0, query: str = None) -> Optional[
        Genre]:
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
        genres = []
        for hit in doc['hits']['hits']:
            genres.append(Genre(**hit["_source"]))
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
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "match_phrase": {
                                        "id": genre_id,
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
        await self.redis.set(genre.id, genre.json(), expire=GENRE_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_genre_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    """Возвращает экземпляр сервиса для работы с жанрами."""
    return GenreService(redis, elastic)
