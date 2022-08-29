from typing import Iterator

from common.models.main import Genre


class Transform:
    """Класс, трансформирующий данные после бд для попадания в elastic."""

    def __init__(self):
        """Инициализирует переменные класса."""
        self.base_dict = {}

    def create_documents(
            self,
            data_generator: Iterator[Genre],
    ):
        """Строит набор документов для записи в elastic.

        Args:
            data_generator: Данные для построения документа
        """
        self.base_dict = {}

        for doc in data_generator:
            es_doc = {
                'id': doc.id,
                'name': doc.name,
                'description': doc.description,
            }
            self.base_dict[doc.id] = es_doc
