import os

from pydantic import BaseSettings


class ETLSettings(BaseSettings):
    """Настройки приложения."""

    postgres_db_name: str = 'movies_database'
    postgres_db_user: str = 'app'
    postgres_db_password: str = '123qwe'
    postgres_db_host: str = '127.0.0.1'
    postgres_db_port: int = 5432  # noqa: WPS432

    data_batch_size: int = 50  # noqa: WPS432

    elastic_url: str = 'http://localhost:9200/'
    path_to_storage_json: str = 'storage.json'

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    class Config(object):
        """Дополнительные базовые настройки."""

        env_file = '.env'
        env_file_encoding = 'utf-8'
