import argparse
import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import multiprocessing
import os
from urllib.request import urlopen
from bs4 import BeautifulSoup
from packages.goodreads_scraper import shelves as gr_shelves
from packages.goodreads_scraper.books import scrape_book
from utils.expo_backoff import ExpoBackoff
from logging import getLogger

from utils.timer import Timer

# Create a logger for this module
logger = getLogger(__name__)


def construct_library(args, queue):
    """Process 1: Scans for indexed pages and appends data to the shared queue."""
    user_id: str = args.user_id
    url = f"https://www.goodreads.com/user/show/{user_id}"
    print(f"Fetching URL: {url}")
    with ExpoBackoff().context():
        source = urlopen(url)
    soup = BeautifulSoup(source, "html.parser")

    shelves_div = soup.find("div", {"id": "shelves"})

    # This is all the shelves a user has
    # we will process each shelf in a thread
    shelf_links = shelves_div.findChildren("a")
    futures = []
    # Create a thread pool executor
    with ThreadPoolExecutor(max_workers=3) as executor:
        for link in shelf_links:
            base_url = link.attrs.get("href")
            shelf: str = re.search(r"\?shelf=([^&]+)", base_url)[1]
            if args.include_shelves is not None and shelf not in args.include_shelves:
                print(f"Skipping shelf '{shelf}'")
                continue
            if shelf in args.exclude_shelves:
                print(f"Skipping shelf '{shelf}'")
                continue
            print(f"Adding shelf '{shelf}' to thread pool.")
            futures.append(executor.submit(gr_shelves.get_shelf, args, shelf))

    for future in as_completed(futures):
        shelf = future.result()
        for book_proc_dto in shelf:
            queue.put(book_proc_dto)

    logger.info(f"Finished getting all shelves plopping the sentinel on there")
    queue.put(None)
    logger.info(f"Finished getting all shelves")


def process_book(args, queue, dlq):
    """Process 2: Takes from the queue and processes data."""
    while True:
        book_proc_dto = queue.get()
        if book_proc_dto is None:
            break  # Stop the loop if None is received, exit process

        logger.debug(f"Processing {book_proc_dto['id']}")
        book_file_path = os.path.join(args.output_dir, f"{book_proc_dto['id']}.json")

        try:
            if os.path.exists(book_file_path):
                logger.debug(f'File {book_file_path} exists, loading and updating')
                with open(book_file_path, 'r') as book_file:
                    existing_book = json.load(book_file)
                existing_book.get('shelves', []).append(book_proc_dto['shelves'])
                book_scrape_dto = existing_book
            else:
                try:
                    logger.debug(f'File {book_file_path} does not exist, scraping')
                    book_scrape_dto = scrape_book(book_proc_dto["id"], args)
                except Exception as e:
                    logger.warning(f"Error scraping book {book_proc_dto['id']}")
                    dlq.put((book_proc_dto, e))
                    continue

            with open(book_file_path, 'w') as book_file:
                json.dump(book_scrape_dto, book_file, indent=2)
        except IOError as e:
            logger.warning(f"Error processing file {book_file_path}")


def dump_queue(queue):
    """
    Empties all pending items in a queue and returns them in a list.
    """
    result = []
    for i in iter(queue.get, None):
        result.append(i)
    # not necessary but releases the GIL
    time.sleep(.1)
    return result


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--user_id",
        type=str,
        default=os.environ.get("GOODREADS_USER_ID"),
    )
    parser.add_argument("--output_dir", type=str, default="goodreads-data")
    parser.add_argument("--skip_user_info", type=bool, default=False)
    parser.add_argument("--include_shelves", type=bool, default=None)
    parser.add_argument("--exclude_shelves", type=list, default=[])
    parser.add_argument("--skip_shelves", type=bool, default=False)
    parser.add_argument("--skip_authors", type=bool, default=False)
    parser.add_argument("--max_pages", type=bool, default=None)

    args = parser.parse_args()
    with Timer():
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
            print(f"Directory '{args.output_dir}' was created.")
        else:
            print(f"Directory '{args.output_dir}' already exists.")

        book_proc_queue = multiprocessing.Queue()
        dlq = multiprocessing.Queue()

        # List to keep track of processes
        processes = []
        num_process_book_workers = 10

        # Creating construct_library worker processes
        p = multiprocessing.Process(target=construct_library, args=(args, book_proc_queue))
        # processes.append(p)
        p.start()
        p.join()
        book_proc_queue.put(None)



        # Creating process_book worker processes
        for _ in range(num_process_book_workers):
            p = multiprocessing.Process(target=process_book, args=(args, book_proc_queue, dlq))
            processes.append(p)
            p.start()

        # Wait for all processes to complete
        for p in processes:
            p.join()

    dlq.put(None)
    logger.info(f"Finished processing all books")

    failures = dump_queue(dlq)
    logger.warning(f"The following could not be processed", len([f[0] for f in failures]))
    with open('failures.json', 'w') as failures_file:
        json.dump({"failed_book_ids": failures}, failures_file, indent=2)

    # finalize_data = dict_merg

    # Signal process 2 to stop
    # book_proc_queue.put(None)
