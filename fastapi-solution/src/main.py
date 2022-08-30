import logging

import aioredis
import uvicorn as uvicorn
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from api.v1 import films, genres, persons
from core.config import get_settings
from core.logger import LOGGING
from db import elastic
from db import redis

conf = get_settings()

app = FastAPI(
    title=conf.PROJECT_NAME,
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
    default_response_class=ORJSONResponse,
)


@app.on_event('startup')
async def startup():
    """Метод, выполняющий инициализацию компонентов приложения при старте."""
    redis.redis = await aioredis.create_redis_pool((conf.REDIS_HOST, conf.REDIS_PORT), minsize=10, maxsize=20)
    elastic.es = AsyncElasticsearch(hosts=[f'http://{conf.ELASTIC_HOST}:{conf.ELASTIC_PORT}'])


@app.on_event('shutdown')
async def shutdown():
    """Метод, выполняющий утилизацию компонентов приложения после завершения работы  приложения."""
    redis.redis.close()
    await redis.redis.wait_closed()
    await elastic.es.close()


app.include_router(films.router, prefix='/api/v1/films', tags=['films'])
app.include_router(genres.router, prefix='/api/v1/genres', tags=['genres'])
app.include_router(persons.router, prefix='/api/v1/persons', tags=['persons'])

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=8000,
        log_config=LOGGING,
        log_level=logging.DEBUG,
    )
