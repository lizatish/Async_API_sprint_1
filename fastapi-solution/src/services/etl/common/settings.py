from pydantic import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения."""

    postgres_db_name: str
    postgres_db_user: str
    postgres_db_password: str
    postgres_db_host: str
    postgres_db_port: int = 5432  # noqa: WPS432

    data_batch_size: int = 50  # noqa: WPS432

    elastic_url: str
    elastic_index_name: str = 'movies'

    path_to_storage_json: str = 'file.json'
    film_work_table_name: str = 'film_work'

    class Config(object):
        """Дополнительные базовые настройки."""

        env_file = '.env'
        env_file_encoding = 'utf-8'


conf = Settings()
