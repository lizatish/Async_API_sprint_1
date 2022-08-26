from psycopg2.extensions import connection as pg_connection

from common.components.base import BaseProducer
from common.models.main import Person, FilmWork, Genre


class PersonProducer(BaseProducer):
    """Главный генератор данных для персон."""

    def __init__(self, connection: pg_connection):
        """Инициализирует соединение к sqlite.

        Args:
            connection: Соединение с sqlite
        """
        super().__init__(connection)

        self.table_name = 'person'
        self.dataclass = Person


class FilmWorkProducer(BaseProducer):
    """Главный генератор данных для кинопроизведений."""

    def __init__(self, connection: pg_connection):
        """Инициализирует соединение к sqlite.

        Args:
            connection: Соединение с sqlite
        """
        super().__init__(connection)

        self.table_name = 'film_work'
        self.dataclass = FilmWork


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
