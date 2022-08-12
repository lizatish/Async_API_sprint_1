import orjson

from pydantic import BaseModel


def orjson_dumps(v, *, default):
    """Функция-подмена для быстрой работы c json."""
    return orjson.dumps(v, default=default).decode()


class Film(BaseModel):
    """Модель кинопроизведения."""

    id: str
    title: str
    description: str

    class Config:
        """Доп. конфигурации для модели кинопроизведения."""

        json_loads = orjson.loads
        json_dumps = orjson_dumps
