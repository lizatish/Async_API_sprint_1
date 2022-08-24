from psycopg2.extensions import connection as pg_connection

from services.etl.common.components.base_producer import BaseProducer
from services.etl.common.models.main import Genre


class GenreProducer(BaseProducer):
    """Главный генератор данных для жанров."""

    def __init__(self, connection: pg_connection):
        """Инициализирует соединение к sqlite.

        Args:
            connection: Соединение с sqlite
        """
        super().__init__(connection)

        self.table_name = 'genre'
        self.dataclass = Genre
