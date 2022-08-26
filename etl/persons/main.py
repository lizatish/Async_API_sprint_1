from elasticsearch import Elasticsearch
from psycopg2.extensions import connection as pg_connection

from common.components.elasticsearch_loader import ElasticsearchLoader
from common.components.producer import PersonProducer
from common.postgres_utils import create_pg_connection
from common.state import State, JsonFileStorage
from persons.settings import conf
from persons.transform import Transform


def run_persons_etl(
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
    producer = PersonProducer(pg_conn)
    transform = Transform()
    elastic_saver = ElasticsearchLoader(es, conf.elastic_index_name, conf.index_json_path)

    latest_genres_state = state.get_state(conf.table_name)

    genres_producer = producer.load_data(batch_size, latest_genres_state)
    for producers_batch in genres_producer:
        genres_list = list(producers_batch)

        transform.create_documents(genres_list)
        elastic_saver.write_to_index(
            transform.base_dict.values(),
        )

        state.set_state(
            conf.table_name,
            genres_list[-1].updated_at.isoformat(),
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
            run_persons_etl(es, pg_conn, portion_size, state)
    pg_conn.close()


if __name__ == '__main__':
    main()
