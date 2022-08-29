import os

from pydantic import BaseSettings


class ETLSettings(BaseSettings):
    """Настройки приложения."""

    postgres_db_name: str
    postgres_db_user: str
    postgres_db_password: str
    postgres_db_host: str = 'postgres'
    postgres_db_port: int = 5432

    data_batch_size: int = 50

    elastic_url: str = 'http://localhost:9200/'
    path_to_storage_json: str = 'storage.json'

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    class Config:
        """Дополнительные базовые настройки."""

        env_file = '.env'
        env_file_encoding = 'utf-8'
