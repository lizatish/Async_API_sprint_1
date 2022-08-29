from http import HTTPStatus

from fastapi import HTTPException


class FilmNotFound(HTTPException):
    """Класс-ответ для случая отсутствия фильма."""

    def __init__(self):
        """Инициализация класса."""
        super().__init__(HTTPStatus.NOT_FOUND, 'Film not found')


class PersonNotFound(HTTPException):
    """Класс-ответ для случая отсутствия участника фильма."""

    def __init__(self):
        """Инициализация класса."""
        super().__init__(HTTPStatus.NOT_FOUND, 'Person not found')


class GenreNotFound(HTTPException):
    """Класс-ответ для случая отсутствия жанра."""

    def __init__(self):
        """Инициализация класса."""
        super().__init__(HTTPStatus.NOT_FOUND, 'Genre not found')
