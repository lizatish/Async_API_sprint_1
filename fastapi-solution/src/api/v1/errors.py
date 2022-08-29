from http import HTTPStatus

from fastapi import HTTPException


class FilmNotFound(HTTPException):
    def __init__(self):
        super().__init__(HTTPStatus.NOT_FOUND, 'Film not found')


class PersonNotFound(HTTPException):
    def __init__(self):
        super().__init__(HTTPStatus.NOT_FOUND, 'Person not found')


class GenreNotFound(HTTPException):
    def __init__(self):
        super().__init__(HTTPStatus.NOT_FOUND, 'Genre not found')
