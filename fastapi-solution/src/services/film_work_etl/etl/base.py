"""Описание базового класса ETL-пайплайна по вычитыванию данных из postgres."""

import psycopg2
from psycopg2.extensions import connection as pg_connection

from services.film_work_etl.logger import get_logger

logger = get_logger()


class BaseExtractor(object):
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
            list_values: list[str],
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
