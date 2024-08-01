from argparse import Namespace
from urllib.request import urlopen

import bs4
from bs4 import BeautifulSoup
from typing import List

from packages.goodreads_scraper.dtos import GoodreadsBookDTO as BookInfo
from utils.expo_backoff import ExpoBackoff
from logging import getLogger

logger = getLogger(__name__)

RATING_STARS_DICT = {
    "it was amazing": 5,
    "really liked it": 4,
    "liked it": 3,
    "it was ok": 2,
    "did not like it": 1,
    "": None,
}


def get_shelf_url(user_id, shelf, page):
    url = (
        "https://www.goodreads.com/review/list/"
        + user_id
        + "?shelf="
        + shelf
        + "&page="
        + str(page)
        + "&per_page="
        + str(100)
        # + "&logger.info=true"
    )
    logger.debug(f"Fetching URL: {url}")
    with ExpoBackoff().context() as backoff:
        source = urlopen(url)
    return BeautifulSoup(source, "html.parser")


def get_id(book_row: bs4.BeautifulSoup) -> str:
    cell = book_row.find("td", {"class": "field title"})
    title_href = cell.find("div", {"class": "value"}).find("a")
    return title_href.attrs.get("href").split("/")[-1]


def get_rating(book_row) -> int:
    cell = book_row.find("td", {"class": "field rating"})
    str_rating = cell.find("div", {"class": "value"}).find("span").attrs.get("title")
    return RATING_STARS_DICT.get(str_rating)


def get_dates_read(book_row):
    cell = book_row.find("td", {"class": "field date_read"})
    dates = cell.find("div", {"class": "value"}).findChildren(
        "div", {"class": "date_row"}
    )
    date_arr = []
    for date in dates:
        date_text = date.text.strip()
        if date_text != "not set":
            date_arr += [date_text]
    return date_arr


def get_shelf(args: Namespace, shelf_name: str) -> List[BookInfo | None]:
    user_id: str = args.user_id
    page = 1
    books_on_shelf: List[BookInfo | None] = list()

    # We don't know how many pages are in this table so we need to loop until we reach the end
    # but remember, we also need to place a None at the end of the queue to signal the end of
    # the queue and process_2 () should stop processing
    while True:
        soup = get_shelf_url(user_id, shelf_name, page)

        # with GenericCache(f"{shelf_name}-{page}.pkl") as cache:
        #     page = cache.get(f"{shelf_name}-{page}.pkl")

        # These are the old lookup indicators... not a fan of them, think we could update them but they work for now
        no_content = soup.find("div", {"class": "greyText nocontent stacked"})
        if no_content or (args.max_pages is not None and page > args.max_pages):
            logger.info(f"🏁 Reached end of content for '{shelf_name}' shelf on page {page}")
            break

        logger.info(f"📖 Scraping '{shelf_name}' shelf page {page}...")
        books_table = soup.find("tbody", {"id": "booksBody"})
        book_rows = books_table.findChildren("tr", recursive=False)

        # Loop through all books in the page
        for book_row in book_rows:
            book_id = get_id(book_row)
            book = {
                "id": get_id(book_row),
                "rating": get_rating(book_row),
                "dates_read": get_dates_read(book_row),
                "shelves": [shelf_name],
            }
            books_on_shelf.append(book)
        page += 1

    logger.info(f"Scraped '{shelf_name}' shelf with {len(books_on_shelf)} books.")
    return books_on_shelf
