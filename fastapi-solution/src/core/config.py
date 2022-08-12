import os
from logging import config as logging_config

from pydantic import BaseSettings

from core.logger import LOGGING


class Settings(BaseSettings):
    """Настройки приложения."""

    # Применяем настройки логирования
    logging_config.dictConfig(LOGGING)

    # Название проекта. Используется в Swagger-документации
    PROJECT_NAME = os.getenv('PROJECT_NAME', 'movies')

    # Настройки Redis
    REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

    # Настройки Elasticsearch
    ELASTIC_HOST = os.getenv('ELASTIC_HOST', '127.0.0.1')
    ELASTIC_PORT = int(os.getenv('ELASTIC_PORT', 9200))

    # Корень проекта
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    class Config(object):
        """Дополнительные базовые настройки."""

        env_file = '.env'
        env_file_encoding = 'utf-8'


conf = Settings()
