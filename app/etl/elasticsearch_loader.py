"""Описание класса ETL-пайплайна по сохранению данных в elasticsearch.."""

from typing import Iterator

import elastic_transport
import elasticsearch
from elasticsearch.helpers import bulk

from app.logger import get_logger
from app.postgres_utils import backoff

logger = get_logger()


class ElasticsearchLoader(object):
    """Класс, реализующий запись данных в elasticsearch."""

    @backoff(elastic_transport.ConnectionError)
    def __init__(self, es: elasticsearch, index_name: str):
        """Инициализирует переменные класса.

        Args:
            es: Объект elasticsearch
            index_name: Название индекса elasticsearch
        """
        self.es = es
        self.index_name = index_name

        if not self.es.indices.exists(index=self.index_name):
            self.create_index()

    @backoff(elastic_transport.ConnectionError)
    def create_index(self):
        """Создает индекс в случае его отсутствия."""
        mappings = {
            'dynamic': 'strict',
            'properties': {
                'id': {
                    'type': 'keyword',
                },
                'imdb_rating': {
                    'type': 'float',
                },
                'genre': {
                    'type': 'keyword',
                },
                'title': {
                    'type': 'text',
                    'analyzer': 'ru_en',
                    'fields': {
                        'raw': {
                            'type': 'keyword',
                        },
                    },
                },
                'description': {
                    'type': 'text',
                    'analyzer': 'ru_en',
                },
                'director': {
                    'type': 'text',
                    'analyzer': 'ru_en',
                },
                'actors_names': {
                    'type': 'text',
                    'analyzer': 'ru_en',
                },
                'writers_names': {
                    'type': 'text',
                    'analyzer': 'ru_en',
                },
                'actors': {
                    'type': 'nested',
                    'dynamic': 'strict',
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'type': 'text',
                            'analyzer': 'ru_en',
                        },
                    },
                },
                'writers': {
                    'type': 'nested',
                    'dynamic': 'strict',
                    'properties': {
                        'id': {
                            'type': 'keyword',
                        },
                        'name': {
                            'type': 'text',
                            'analyzer': 'ru_en',
                        },
                    },
                },
            },
        }

        settings = {
            'refresh_interval': '1s',
            'analysis': {
                'filter': {
                    'english_stop': {
                        'type': 'stop',
                        'stopwords': '_english_',
                    },
                    'english_stemmer': {
                        'type': 'stemmer',
                        'language': 'english',
                    },
                    'english_possessive_stemmer': {
                        'type': 'stemmer',
                        'language': 'possessive_english',
                    },
                    'russian_stop': {
                        'type': 'stop',
                        'stopwords': '_russian_',
                    },
                    'russian_stemmer': {
                        'type': 'stemmer',
                        'language': 'russian',
                    },
                },
                'analyzer': {
                    'ru_en': {
                        'tokenizer': 'standard',
                        'filter': [
                            'lowercase',
                            'english_stop',
                            'english_stemmer',
                            'english_possessive_stemmer',
                            'russian_stop',
                            'russian_stemmer',
                        ],
                    },
                },
            },
        }
        self.es.indices.create(
            index=self.index_name,
            ignore=400,
            mappings=mappings,
            settings=settings,
        )

    @backoff(elastic_transport.ConnectionError)
    def write_to_index(self, docs: list[dict]):
        """Записывает подготовленные документы в elasticsearch.

        Args:
            docs: Подготовленные документы для записи в elasticsearch
        """
        bulk(self.es, self.generate_data(docs))
        docs_size = len(docs)
        logger.warning(f'Write {docs_size} docs into elastic.')

    def generate_data(self, docs: list[dict]) -> Iterator[dict]:
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
