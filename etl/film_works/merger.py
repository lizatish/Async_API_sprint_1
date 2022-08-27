import dataclasses

from psycopg2.extensions import connection as pg_connection

from common.components.base import BaseExtractor
from common.models.utils_sql import MergeResult
from common.utils.convert import convert_sql2models


class Merger(BaseExtractor):
    """Класс, реализующий составляющую склейки данных ETL-пайплайна."""

    def __init__(
            self,
            connection: pg_connection,
    ):
        """Инициализирует переменные класса.

        Args:
            connection: Соединение c postgresql
        """
        super().__init__(connection)
        self.dataclass = MergeResult

    def load_data(self, fw_ids: list[str], batch_size: int):
        """Загружает данные из связанной таблицы через m2m связь.

         Args:
            fw_ids: Идентификаторы таблицы кинопроизведений
            batch_size: Размер результирующего батча

        Yields:
            Iterator[tuple]: батч с данными в виде кортежей
        """
        with self.connection.cursor() as cursor:
            sql_values_format = self.set_values_sql_format(cursor, fw_ids)

            column_names = [
                field.name for field in
                dataclasses.fields(self.dataclass)
            ]

            select_fields = [
                'fw.id',
                'fw.title',
                'fw.description',
                'fw.rating',
                'fw.type',
                'fw.created_at',
                'fw.updated_at',
                'pfw.role',
                'p.id',
                'p.full_name',
                'g.name',
                'g.id',
            ]

            select_sql_str = ', '.join([f'{select_field} as {model_field_name}'
                                        for select_field, model_field_name in
                                        zip(select_fields, column_names)
                                        ])

            sql = f"""SELECT {select_sql_str}
            FROM content.film_work fw
            LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
            LEFT JOIN content.person p ON p.id = pfw.person_id
            LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
            LEFT JOIN content.genre g ON g.id = gfw.genre_id
            WHERE fw.id IN {sql_values_format};
            """

            self.execute(cursor, sql)
            batch = cursor.fetchmany(batch_size)
            while batch:
                yield convert_sql2models(
                    self.dataclass,
                    column_names,
                    batch,
                )
                batch = cursor.fetchmany(batch_size)
