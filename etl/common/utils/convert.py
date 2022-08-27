"""Модуль конвертации данных."""
from typing import Iterator, List

import pydantic
from pydantic.dataclasses import dataclass

from common.logger import get_logger

logger = get_logger()


def convert_sql2models(
        class_type: dataclass,
        column_names: List[str],
        db_rows: List[tuple],
) -> Iterator[dataclass]:
    """Конвертирует сырые данные из базы в модели dataclass.

    Args:
        class_type: Dataclass, соответствующей таблице с данными
        column_names: Названия колонок базы
        db_rows: Данные из базы

    Yields:
         Iterator[dataclass]: итератор модели dataclass
    """
    for row in db_rows:
        model_dict = {
            col_name: row_val
            for col_name, row_val in zip(column_names, row)
        }
        try:
            yield class_type(**model_dict)
        except pydantic.ValidationError as err:
            logger.error(err)
