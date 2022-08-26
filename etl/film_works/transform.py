from typing import Iterator

from common.models.utils_sql import MergeResult


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
                        'genres': [],
                        'genres_names': [],
                        'directors': [],
                        'directors_names': [],
                        'actors': [],
                        'actors_names': [],
                        'writers': [],
                        'writers_names': [],
                    }
                else:
                    es_doc = self.base_dict[doc.film_work_id]
                    es_doc |= {
                        'id': doc.film_work_id,
                        'imdb_rating': doc.film_work_rating,
                        'title': doc.film_work_title,
                        'description': doc.film_work_description,
                    }

                es_person_enrich_doc = self.add_addition_person_info(doc, es_doc)
                es_ready_doc = self.add_addition_genres_info(doc, es_person_enrich_doc)

                self.base_dict[doc.film_work_id] = es_ready_doc

    def add_addition_person_info(
            self,
            doc: MergeResult,
            output_doc: dict,
    ) -> dict:
        """Обогащает документы эластика дополнительными данными по персонам.

        Args:
            doc: Обогащающие документы
            output_doc: Результирующие документы

        Returns:
            dict: Обогащенный словарь для elastic
        """

        if doc.pfw_role:
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

    def add_addition_genres_info(
            self,
            doc: MergeResult,
            output_doc: dict,
    ) -> dict:
        """Обогащает документы эластика дополнительными данными по жанрам.

        Args:
            doc: Обогащающие документы
            output_doc: Результирующие документы

        Returns:
            dict: Обогащенный словарь для elastic
        """
        output_doc['genres'].append(
            {
                'id': doc.genre_id,
                'name': doc.genre_name,
            },
        )
        output_doc['genres_names'].append(
            doc.genre_name,
        )

        return output_doc
