from typing import Iterator

from common.models.main import Person


class Transform:
    """Класс, трансформирующий данные после бд для попадания в elastic."""

    def __init__(self):
        """Инициализирует переменные класса."""
        self.base_dict = {}

    def create_documents(
            self,
            data_generator: Iterator[Person],
    ):
        """Строит набор документов для записи в elastic.

        Args:
            data_generator: Данные для построения документа
        """
        self.base_dict = {}

        for doc in data_generator:
            es_doc = {
                'id': doc.id,
                'full_name': doc.full_name,
            }
            self.base_dict[doc.id] = es_doc
