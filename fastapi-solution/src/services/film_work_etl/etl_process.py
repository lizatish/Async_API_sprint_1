from elasticsearch import Elasticsearch
from psycopg2.extensions import connection as pg_connection

from services.film_work_etl.etl.elasticsearch_loader import ElasticsearchLoader
from services.film_work_etl.etl.enricher import Enricher
from services.film_work_etl.etl.merger import Merger
from services.film_work_etl.etl.producer import (
    PersonProducer,
    FilmWorkProducer,
)
from services.film_work_etl.etl.transform import Transform
from services.film_work_etl.postgres_utils import create_pg_connection
from services.film_work_etl.settings import conf
from services.film_work_etl.state import State, JsonFileStorage


def run_film_works_etl(
        es: Elasticsearch,
        pg_conn: pg_connection,
        batch_size: int,
        state: State,
):
    """Запускает ETL-процесс для кинопроизведений.

    Args:
        es: Объект elasticsearch
        pg_conn: Соединение к postgres
        batch_size: Размер батча
        state: Хранилище состояния
    """
    producer = FilmWorkProducer(pg_conn)
    merger = Merger(pg_conn)
    transform = Transform()
    elastic_saver = ElasticsearchLoader(es, conf.elastic_index_name)

    latest_person_state = state.get_state(conf.film_work_table_name)

    fw_producer_loader = producer.load_data(batch_size, latest_person_state)
    for fw_batch in fw_producer_loader:
        fws_list = list(fw_batch)
        fw_ids = [fw.id for fw in fws_list]

        merge_data_loader = merger.load_data(fw_ids, batch_size)
        transform.create_documents(merge_data_loader)
        elastic_saver.write_to_index(
            transform.base_dict.values(),
        )

        state.set_state(
            conf.film_work_table_name,
            fws_list[-1].updated_at.isoformat(),
        )


def run_universal_etl(
        es: Elasticsearch,
        pg_conn: pg_connection,
        batch_size: int,
        state: State,
        producer_table_name: str,
        m2m_table_name: str,
):
    """Запускает ETL-процесс для участников фильма.

    Args:
        es: Объект elasticsearch
        pg_conn: Соединение к postgres
        batch_size: Размер батча
        state: Хранилище состояния
        producer_table_name: название таблицы producer-а
        m2m_table_name: название связующей m2m таблицы для enricher
    """
    producer = PersonProducer(pg_conn)
    enricher = Enricher(
        m2m_table_name,
        producer_table_name,
        conf.film_work_table_name,
        pg_conn,
    )
    merger = Merger(pg_conn)
    transform = Transform()
    elastic_saver = ElasticsearchLoader(es, conf.elastic_index_name)

    latest_producer_state = state.get_state(producer_table_name)

    producers_loader = producer.load_data(
        batch_size,
        latest_producer_state,
    )
    for producers_batch in producers_loader:
        producers_list = list(producers_batch)
        producers_ids = [producer.id for producer in producers_list]

        fw_generator = enricher.load_data(producers_ids, batch_size)
        for fw_batch in fw_generator:
            fws_list = list(fw_batch)
            fw_ids = [fw.id for fw in fws_list]
            persons_merger_loader = merger.load_data(fw_ids, batch_size)

            transform.create_documents(persons_merger_loader)
            elastic_saver.write_to_index(
                transform.base_dict.values(),
            )
        state.set_state(
            producer_table_name,
            producers_list[-1].updated_at.isoformat(),
        )


def main():
    """Главная функция запуска приложения."""
    dsl = {
        'dbname': conf.postgres_db_name,
        'user': conf.postgres_db_user,
        'password': conf.postgres_db_password,
        'host': conf.postgres_db_host,
        'port': conf.postgres_db_port,
    }
    pg_conn = create_pg_connection(dsl)

    storage = JsonFileStorage(conf.path_to_storage_json)
    state = State(storage)
    portion_size = conf.data_batch_size
    es = Elasticsearch(conf.elastic_url)
    with pg_conn:
        while True:
            run_universal_etl(
                es,
                pg_conn,
                portion_size,
                state,
                'genre',
                'genre_film_work',
            )
            run_universal_etl(
                es,
                pg_conn,
                portion_size,
                state,
                'person',
                'person_film_work',
            )
            run_film_works_etl(es, pg_conn, portion_size, state)
    pg_conn.close()


if __name__ == '__main__':
    main()