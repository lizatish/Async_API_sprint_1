import orjson
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    """Функция-подмена для быстрой работы c json."""
    return orjson.dumps(v, default=default).decode()


class UUIDMixin(BaseModel):
    """Базовая модель."""

    id: str

    class Config:
        """Доп. конфигурации для базовой модели."""

        allow_population_by_field_name = True
        json_loads = orjson.loads
        json_dumps = orjson_dumps
