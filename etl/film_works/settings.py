from common.etl_settings import ETLSettings


class FilmWorksSettings(ETLSettings):
    """Настройки приложения."""

    elastic_index_name: str = 'movies'
    index_json_path: str = 'app/indices/movies.json'
    table_name: str = 'film_work'


conf = FilmWorksSettings()
