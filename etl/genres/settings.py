from common.etl_settings import ETLSettings


class GenresSettings(ETLSettings):
    """Настройки приложения."""

    elastic_index_name: str = 'genres'
    index_json_path: str = 'app/indices/genre.json'

    table_name: str = 'genres'


conf = GenresSettings()
