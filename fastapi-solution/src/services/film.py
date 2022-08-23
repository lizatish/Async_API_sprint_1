from functools import lru_cache
from typing import Optional, List

from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.film import Film

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, film_id: str) -> Optional[Film]:
        film = await self._film_from_cache(film_id)
        if not film:
            film = await self._get_film_from_elastic(film_id)
            if not film:
                return None
            await self._put_film_to_cache(film)
        return film

    async def get_scope_films(self, from_: int, size: int, filter: dict, sort: str = 'imdb_rating') -> Optional[List[Film]]:
        films = await self._get_scope_films_from_elastic(from_=from_, size=size, sort=sort, filter=filter)
        if not films:
            return None
        return films

    async def search_film(self, query: str,  from_: int, size: int) -> Optional[List[Film]]:
        films = await self._search_film_from_elastic(query=query, from_=from_, size=size)
        if not films:
            return None
        return films

    async def _search_film_from_elastic(self, query: str, from_: int, size: int) -> Optional[List[Film]]:
        try:
            doc = await self.elastic.search(index="movies", from_=from_, size=size, body={
                "query": {
                    "multi_match": {
                        "query": f"{query}", 
                        "fuzziness": "auto"
                    }
                }
            },)
        except NotFoundError:
            return None
        return [Film(**hit["_source"]) for hit in doc['hits']['hits']]

    async def _get_scope_films_from_elastic(self, from_: int, size: int, filter: dict, sort: str = '-imdb_rating') -> Optional[List[Film]]:
        if sort:
            sorted = f'{sort[1:]}:desc' if sort[0] == '-' else f'{sort}:asc'
        else:
            sorted = 'imdb_rating:desc'
        try:
            if filter:
                body = [{
                        "nested": {
                            "path": f"{key}",
                            "query": {
                                "bool": {
                                "must": [
                                    { "match": { f"{key}.id": f"{filter[key]}" } }
                                ]
                                }
                            }
                        }
                    } for key in filter]
                print(body)
                doc = await self.elastic.search(
                    index='movies',
                    from_=from_,
                    size=size,
                    sort=sorted,
                    body= {
                        "query": {"bool": {"must": body}}
                        }
                )
            else:
                doc = await self.elastic.search(
                    index='movies',
                    from_=from_,
                    size=size,
                    sort=sorted
                )
                print(doc)
        except NotFoundError:
            return None
        return [Film(**hit["_source"]) for hit in doc['hits']['hits']]

    async def _get_film_from_elastic(self, film_id: str) -> Optional[Film]:
        try:
            doc = await self.elastic.get('movies', film_id)
        except NotFoundError:
            return None
        return Film(**doc['_source'])

    async def _film_from_cache(self, film_id: str) -> Optional[Film]:
        data = await self.redis.get(film_id)
        if not data:
            return None


        film = Film.parse_raw(data)
        return film

    async def _put_film_to_cache(self, film: Film):
        await self.redis.set(film.uuid, film.json(), expire=FILM_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)