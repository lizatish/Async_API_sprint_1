from typing import Iterator

from app.models.main import RoleType
from app.models.utils_sql import MergeResult


class Transform(object):
    """Класс, трансформирующий данные после бд для попадания в elastic."""

    def __init__(self):
        """Инициализирует переменные класса."""
        self.base_dict = {}

    def create_documents(
            self,
            merge_data_generator: Iterator[Iterator[MergeResult]],
    ):
        """Строит набор документов для записи в elastic.

        Args:
            merge_data_generator: Данные для построения документа
        """
        self.base_dict = {}

        for merge_batch in merge_data_generator:
            for doc in merge_batch:
                if doc.film_work_id not in self.base_dict:
                    es_doc = {
                        'id': doc.film_work_id,
                        'imdb_rating': doc.film_work_rating,
                        'title': doc.film_work_title,
                        'description': doc.film_work_description,
                        'genre': [doc.genre_name],
                        'director': [],
                        'actors_names': [],
                        'writers_names': [],
                        'actors': [],
                        'writers': [],
                    }
                else:
                    es_doc = self.base_dict[doc.film_work_id]
                    es_doc |= {
                        'id': doc.film_work_id,
                        'imdb_rating': doc.film_work_rating,
                        'title': doc.film_work_title,
                        'description': doc.film_work_description,
                    }

                es_doc = self.add_addition_info(doc, es_doc)

                self.base_dict[doc.film_work_id] = es_doc

    def add_addition_info(
            self,
            doc: MergeResult,
            output_doc: dict,
    ) -> dict:
        """Обогащает документы эластика дополнительными данными.

        Args:
            doc: Обогащающие документы
            output_doc: Результирующие документы

        Returns:
            dict: Обогащенный словарь для elastic
        """
        not_main_roles = [RoleType.actor, RoleType.writer]
        if doc.pfw_role == RoleType.director:
            if doc.person_full_name not in output_doc[doc.pfw_role]:
                output_doc[doc.pfw_role].append(doc.person_full_name)
        elif doc.pfw_role in not_main_roles:
            role_case_name = f'{doc.pfw_role}s'
            names_case_name = f'{role_case_name}_names'

            if doc.person_full_name not in output_doc[names_case_name]:
                output_doc[names_case_name].append(
                    doc.person_full_name,
                )

                output_doc[role_case_name].append(
                    {
                        'id': doc.person_id,
                        'name': doc.person_full_name,
                    },
                )
        return output_doc
