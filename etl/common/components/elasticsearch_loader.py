"""Описание класса ETL-пайплайна по сохранению данных в elasticsearch.."""
import json
from typing import Iterator, List

import elastic_transport
import elasticsearch
from elasticsearch.helpers import bulk

from common.logger import get_logger
from common.postgres_utils import backoff

logger = get_logger()


class ElasticsearchLoader:
    """Класс, реализующий запись данных в elasticsearch."""

    @backoff(elastic_transport.ConnectionError)
    def __init__(self, es: elasticsearch, index_name: str, json_path: str):
        """Инициализирует переменные класса.

        Args:
            es: Объект elasticsearch
            index_name: Название индекса elasticsearch
        """
        self.es = es
        self.index_name = index_name
        self.index_json_path = json_path
        if not self.es.indices.exists(index=self.index_name):
            self.create_index()

    @backoff(elastic_transport.ConnectionError)
    def create_index(self):
        """Создает индекс в случае его отсутствия."""
        with open(self.index_json_path, 'r') as index_file:
            index_dict = json.load(index_file)

            self.es.indices.create(
                index=self.index_name,
                ignore=400,
                **index_dict,
            )

    @backoff(elastic_transport.ConnectionError)
    def write_to_index(self, docs: List[dict]):
        """Записывает подготовленные документы в elasticsearch.

        Args:
            docs: Подготовленные документы для записи в elasticsearch
        """
        bulk(self.es, self.generate_data(docs))
        docs_size = len(docs)
        logger.warning(f'Write {docs_size} docs into elastic.')

    def generate_data(self, docs: List[dict]) -> Iterator[dict]:
        """Генерирует документы для bulk запроса.

        Args:
            docs: Подготовленные документы для записи в elasticsearch

        Yields:
            Iterator[dict]: Итератор словарей для bulk запроса
        """
        for doc in docs:
            yield {
                '_op_type': 'index',
                '_id': doc['id'],
                '_index': self.index_name,
                '_source': doc,
            }
