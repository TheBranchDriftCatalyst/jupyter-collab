from typing import List, Optional, Any
from pydantic import BaseModel, HttpUrl


class GoodreadsSeriesDTO(BaseModel):
    primary_works: int
    series_name: Optional[str] = None
    series_url: str
    total_works: int


class GoodreadsBookDTO(BaseModel):
    author: str
    description: str
    genres: List[str]
    id: str
    image: str
    num_pages: int
    num_ratings: int
    num_reviews: int
    number_in_series: Optional[float] = None  # Optional because some books might not be part of a series
    series: Optional[GoodreadsSeriesDTO] = None  # Optional because not all books are part of a series
    title: str
    url: HttpUrl


class NotionBookDTO(GoodreadsBookDTO):
    pass



class NotionSeriesDTO(GoodreadsSeriesDTO):
    pass
