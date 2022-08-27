from typing import Iterator

from psycopg2.extensions import connection as pg_connection

from common.components.base import BaseExtractor
from common.models.utils_sql import EnrichResult
from common.utils.convert import convert_sql2models


class Enricher(BaseExtractor):
    """Класс, обогащающий основную информацию для etl-пайплайна."""

    def __init__(
            self,
            table_name: str,
            producer_table_name: str,
            enrich_table_name: str,
            connection: pg_connection,
    ):
        """Инициализирует переменные класса.

        Args:
            table_name: Название таблицы many2many
            producer_table_name: Название таблицы producer-а
            enrich_table_name: Название связанной таблицы через m2m
            connection: Соединение c postgresql
        """
        super().__init__(connection)

        self.table_name = table_name
        self.producer_table_name = producer_table_name
        self.enrich_table_name = enrich_table_name
        self.dataclass = EnrichResult

    def load_data(
            self,
            producer_ids: list[str],
            batch_size: int,
    ) -> Iterator[tuple]:
        """Загружает данные из связанной таблицы через m2m связь.

        Args:
            producer_ids: Идентификаторы таблицы producer-d
            batch_size: Размер результирующего батча

         Yields:
            Iterator[tuple]: батч с данными в виде кортежей
        """
        with self.connection.cursor() as cursor:
            sql_values_format = self.set_values_sql_format(
                cursor,
                producer_ids,
            )

            sql = cursor.mogrify(
                f'SELECT enrch.id, enrch.updated_at '
                f'FROM content.{self.enrich_table_name} as enrch '
                f'LEFT JOIN content.{self.table_name} as m2m '
                f'ON m2m.{self.enrich_table_name}_id = enrch.id '
                f'WHERE m2m.{self.producer_table_name}_id '
                f'IN {sql_values_format} '
                f'ORDER BY enrch.updated_at',
                f'LIMIT {batch_size};',
            )

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
