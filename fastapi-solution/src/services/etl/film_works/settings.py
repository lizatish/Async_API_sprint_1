from services.etl.common.etl_settings import ETLSettings


class FilmWorksSettings(ETLSettings):
    """Настройки приложения."""

    elastic_index_name: str = 'movies'
    index_json_path: str = ''.join(['/Users/lizatish/PycharmProjects/Async_API_sprint_1/',
                                    'fastapi-solution/src/services/etl/indices/movies.json'])
    table_name: str = 'film_work'


conf = FilmWorksSettings()
