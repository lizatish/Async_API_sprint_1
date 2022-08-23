from typing import List, Optional
from pydantic import BaseModel, Field


class RelatedFieldsMixin(BaseModel):
    uuid: str
    full_name: str
    films_ids: list
    role: str


class Writers(RelatedFieldsMixin):
    pass

class Actors(RelatedFieldsMixin):
    pass

class Genre(BaseModel):
    uuid: str
    name: str

class Directors(RelatedFieldsMixin):
    pass


class Film(BaseModel):
    uuid: str
    title: str
    imdb_rating: float
    description: Optional[str]
    genre: List[Genre] = []
    actors: List[Actors] = []
    writers: List[Writers] = []
    directors: List[Directors] = [] #= Directors()
    # creation_date: date = None

class ShortFilm(BaseModel):
    uuid: str
    title: str
    imdb_rating: float