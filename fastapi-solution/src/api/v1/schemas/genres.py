from pydantic import BaseModel


class Genre(BaseModel):
    """Модель жанра для ответа пользователю."""

    uuid: str
    name: str
