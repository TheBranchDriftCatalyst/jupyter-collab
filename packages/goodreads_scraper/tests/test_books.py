import json
import os
import sys
import pytest
import pytest_snapshot
from icecream import ic

from packages.goodreads_scraper import books as gr_books


@pytest.mark.snapshot
def test_scrape_book(snapshot: pytest_snapshot) -> None:
    # Call your function
    book_info = gr_books.scrape_book(
        "13999.To_Light_a_Candle", args={"output_dir": "data"}
    )
    snapshot.assert_match(
        book_info.model_dump_json(indent=3), "book_info.json",
    )
