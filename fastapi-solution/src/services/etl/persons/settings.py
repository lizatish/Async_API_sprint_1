from services.etl.common.etl_settings import ETLSettings


class GenresSettings(ETLSettings):
    """Настройки приложения."""

    elastic_index_name: str = 'persons'
    index_json_path: str = ''.join(['/Users/lizatish/PycharmProjects/Async_API_sprint_1/',
                                    'fastapi-solution/src/services/etl/indices/persons.json'])

    table_name: str = 'persons'


conf = GenresSettings()
