import os
from functools import lru_cache
from logging import config as logging_config

from pydantic import BaseSettings

from core.logger import LOGGING


class Settings(BaseSettings):
    """Настройки приложения."""

    # Применяем настройки логирования
    logging_config.dictConfig(LOGGING)

    # Название проекта. Используется в Swagger-документации
    PROJECT_NAME: str = 'movies'

    # Настройки Redis
    REDIS_HOST: str = 'redis'
    REDIS_PORT: int = 6379

    # Настройки Elasticsearch
    ELASTIC_HOST: str = 'elastic'
    ELASTIC_PORT: int = 9200

    # Корень проекта
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Время хранения данных в кэше
    FILM_CACHE_EXPIRE_IN_SECONDS: int = 60 * 5
    GENRE_CACHE_EXPIRE_IN_SECONDS: int = 60 * 5
    PERSON_CACHE_EXPIRE_IN_SECONDS: int = 60 * 5

    class Config:
        """Дополнительные базовые настройки."""

        env_file = '.env'
        env_file_encoding = 'utf-8'


@lru_cache()
def get_settings():
    return Settings()
