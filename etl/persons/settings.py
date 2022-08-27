from common.etl_settings import ETLSettings


class GenresSettings(ETLSettings):
    """Настройки приложения."""

    elastic_index_name: str = 'persons'
    index_json_path: str = 'app/indices/persons.json'

    table_name: str = 'persons'


conf = GenresSettings()
