"""Описание базового класса ETL-пайплайна по вычитыванию данных из postgres."""

from datetime import datetime
from typing import Iterator, Optional, List

import psycopg2
from psycopg2.extensions import connection as pg_connection
from pydantic.dataclasses import dataclass

from common.logger import get_logger
from common.utils.convert import convert_sql2models

logger = get_logger()


class BaseExtractor:
    """Базовый класс ETL-пайплайна для работы с postgres."""

    def __init__(self, connection: pg_connection):
        """Инициализирует переменные класса.

        Args:
            connection: Соединение с postgresql
        """
        self.connection = connection
        self.table_name = ''

    def execute(
            self,
            cursor: psycopg2.extensions.cursor,
            sql: str,
    ):
        """Выполняет запрос, обрабатывая ошибки выполнения.

        Args:
            cursor: Курсор к базе данных
            sql: Строка запросы
        """
        try:
            cursor.execute(sql)
        except psycopg2.IntegrityError as err:
            self.connection.rollback()
            err_description = err.args[0]
            logger.error(
                'Postgres error occurred from table %s: %s',
                self.table_name,
                err_description,
            )

    def set_values_sql_format(
            self,
            cursor: psycopg2.extensions.cursor,
            list_values: List[str],
    ) -> str:
        """Форматирует кортежи данных для возможности записывать данные пачкой.

        Args:
            cursor: Курсор к базе данных
            list_values: Список строк для заполнения базы

        Returns:
             str: Отформатированная строка с данными для заполнения базы
        """
        str_format = ', '.join(['%s' for _ in range(len(list_values))])
        return cursor.mogrify(f'({str_format})', list_values).decode('utf-8')


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
    ) -> Iterator[List[dataclass]]:
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
