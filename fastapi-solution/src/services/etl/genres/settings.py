from services.etl.common.etl_settings import ETLSettings


class GenresSettings(ETLSettings):
    """Настройки приложения."""

    elastic_index_name: str = 'genres'
    index_json_path: str = ''.join(['/Users/lizatish/PycharmProjects/Async_API_sprint_1/',
                                    'fastapi-solution/src/services/etl/indices/genre.json'])

    table_name: str = 'genres'


conf = GenresSettings()
