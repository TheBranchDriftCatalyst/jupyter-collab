from argparse import Namespace
import json
import logging
from urllib.request import urlopen
import os
from bs4 import BeautifulSoup
import re

from goodreads_scraper import books
from expo_backoff import ExpoBackoff


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
        + "&print=true"
    )
    with ExpoBackoff().context() as backoff:
        source = urlopen(url)
    return BeautifulSoup(source, "html.parser")


def get_id(book_row):
    cell = book_row.find("td", {"class": "field title"})
    title_href = cell.find("div", {"class": "value"}).find("a")
    return title_href.attrs.get("href").split("/")[-1]


def get_rating(book_row):
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


def get_shelf(
    args: Namespace,
    shelf: str,
):
    user_id: str = args.user_id
    output_dir: str = f"{args.output_dir}books/"
    page = 1
    books_on_shelf = set()
    extra_book_data = {}  # book_id -> [shelf1, shelf2, ...]

    while True:
        soup = get_shelf_url(user_id, shelf, page)

        no_content = soup.find("div", {"class": "greyText nocontent stacked"})
        if no_content or (page == 2):
            print(f"🏁 Reached end of content for '{shelf}' shelf.")
            break

        books_table = soup.find("tbody", {"id": "booksBody"})
        book_rows = books_table.findChildren("tr", recursive=False)

        # Loop through all books in the page
        for book_row in book_rows:
            book_id = get_id(book_row)
            shelf_data = extra_book_data[book_id] = extra_book_data.get(book_id, [])
            shelf_data.append(shelf)
            books_on_shelf.add(book_id)
            # file_path = output_dir + book_id + ".json"

            # If the book has already been scraped, just add the shelf
            # if book_id in books_on_shelf:
            #     # with open(file_path, "r") as file:
            #     book = json.load(file)
            #     if shelf not in book["shelves"]:
            #         book["shelves"].append(shelf)
            #         print("✅ Updated " + book_id)
            #         # changed = True
            # else:
            #     book = books.scrape_book(book_id, args)
            #     book["rating"] = get_rating(book_row)
            #     book["dates_read"] = get_dates_read(book_row)
            #     book["shelves"] = [shelf]
            #     print(f"🎉 Scraped {book_id}")
            # changed = True

            # if changed:
            #     # Write the json file for the book
            #     file = open(file_path, "w")
            #     json.dump(book, file, indent=2)
            #     file.close()

        page += 1

    print(f"Scraping '{shelf}' shelf...")
    return books_on_shelf, extra_book_data


# def get_all_shelves(args: Namespace):
#     if args.skip_shelves:
#         return

#     user_id: str = args.user_id
#     output_dir: str = args.output_dir + "books/"
#     url = "https://www.goodreads.com/user/show/" + user_id
#     with ExpoBackoff().context() as backoff:
#         source = urlopen(url)
#     soup = BeautifulSoup(source, "html.parser")

#     os.makedirs(output_dir, exist_ok=True)

#     shelves_div = soup.find("div", {"id": "shelves"})
#     shelf_links = shelves_div.findChildren("a")

#     for link in shelf_links:
#         base_url = link.attrs.get("href")
#         shelf: str = re.search(r"\?shelf=([^&]+)", base_url).group(1)
#         get_shelf(args, shelf)


from concurrent.futures import ThreadPoolExecutor, as_completed

# import re
# import os
# from urllib.request import urlopen
# from bs4 import BeautifulSoup
# from argparse import Namespace


def get_all_shelves_threaded(args: Namespace, exclude_shelves=None):
    if exclude_shelves is None:
        exclude_shelves = []
    if args.skip_shelves:
        return

    user_id: str = args.user_id
    # output_dir: str = args.output_dir + "books/"
    url = f"https://www.goodreads.com/user/show/{user_id}"
    print(f"Fetching URL: {url}")
    with ExpoBackoff().context() as backoff:
        source = urlopen(url)
    soup = BeautifulSoup(source, "html.parser")

    # os.makedirs(output_dir, exist_ok=True)

    shelves_div = soup.find("div", {"id": "shelves"})
    shelf_links = shelves_div.findChildren("a")
    futures = []
    # Create a thread pool executor
    with ThreadPoolExecutor(max_workers=20) as executor:
        for link in shelf_links:
            base_url = link.attrs.get("href")
            shelf: str = re.search(r"\?shelf=([^&]+)", base_url)[1]
            if shelf in exclude_shelves or shelf not in include_shelves:
                print(f"Skipping shelf '{shelf}'")
                continue
            print(f"Adding shelf '{shelf}' to thread pool.")
            # Submit tasks to the thread pool
            get_shelf(args, shelf)
            futures.append(executor.submit(get_shelf, args, shelf))
        # Wait for all tasks to complete
        # for future in futures:
        #     future.result()
        return futures
