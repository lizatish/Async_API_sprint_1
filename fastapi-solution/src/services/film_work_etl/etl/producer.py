from datetime import datetime
from typing import Iterator, Optional

from psycopg2.extensions import connection as pg_connection
from pydantic.dataclasses import dataclass

from services.film_work_etl.etl.base import BaseExtractor
from services.film_work_etl.models.main import Person, FilmWork, Genre
from services.film_work_etl.utils.convert import convert_sql2models


class BaseProducer(BaseExtractor):
    """Базовый класс для генераторов данных."""

    def __init__(self, connection: pg_connection):
        """Инициализирует переменные класса.

        Args:
            connection: Соединение с postgresql
        """
        super().__init__(connection)

        self.table_name: str = ''
        self.dataclass: dataclass = None

    def load_data(
            self,
            batch_size: int,
            start_from: Optional[datetime],
    ) -> Iterator[list[dataclass]]:
        """Производит загрузку данных.

        Args:
            batch_size: Размер порции данных
            start_from: Время последнего изменения данных

        Yields:
             Iterator[list[FilmWork]]:
             Итератор с порцией данных в формате dataclass
        """
        with self.connection.cursor() as cursor:
            updated_at_from_field = ''
            if start_from:
                updated_at_from_field = f"WHERE updated_at >= '{start_from}'"
            sql = cursor.mogrify(f"""SELECT * FROM {self.table_name}
            {updated_at_from_field} ORDER BY updated_at;""")
            self.execute(cursor, sql)

            column_names = [
                cursor_data[0]
                for cursor_data in cursor.description
            ]
            batch = cursor.fetchmany(batch_size)
            while batch:
                yield convert_sql2models(
                    self.dataclass,
                    column_names,
                    batch,
                )
                batch = cursor.fetchmany(batch_size)


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
