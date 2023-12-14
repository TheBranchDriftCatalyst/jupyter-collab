import os
import sys
import pytest

cwd = os.getcwd()
repo_root = os.path.abspath(os.path.join(cwd, "../.."))
sys.path.append(repo_root)
print(repo_root)


import goodreads_scraper.books as gr_books


@pytest.mark.snapshot
def test_book_info(snapshot):
    # Call your function
    result = gr_books.scrape_book(
        "13999.To_Light_a_Candle", args={"output_dir": "data"}
    )
    # Compare the result with the snapshot
    snapshot.assert_match(result)
