import argparse
import sys
import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import multiprocessing
import os
from urllib.request import urlopen
from bs4 import BeautifulSoup
from icecream import ic

from packages.goodreads_scraper import shelves as gr_shelves
from packages.goodreads_scraper.books import scrape_book
from packages.goodreads_scraper.dtos import GoodreadsBookDTO as BookInfo
from utils.cache import GenericCache
from utils.expo_backoff import ExpoBackoff
from logging import getLogger

from utils.timer import Timer

from typing import Any, Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import re
import os
import logging
from urllib.request import urlopen
from bs4 import BeautifulSoup

# Create a logger for this module
logger = getLogger(__name__)


def construct_library(cli_args: argparse.Namespace, scrape_book_queue: Queue) -> None:
    """
    Process 1: Scans user's shelves on Goodreads for indexed pages and appends data to the shared scrape_book_queue.

    Args:
        cli_args (Dict[str, Any]): A dictionary containing configuration arguments. Keys include user_id, include_shelves,
                               and exclude_shelves.
        scrape_book_queue (Queue): A queue for processing books. Each book is represented as a dictionary.

    Raises:
        ValueError: If user_id is not provided in cli_args.
    """

    user_id: Optional[str] = cli_args.get("user_id")
    if user_id is None:
        raise ValueError(
            "A user_id must be provided either as an argument or as an environment variable."
        )

    url = f"https://www.goodreads.com/user/show/{user_id}"
    logger.debug(f"Fetching URL: {url}")
    with ExpoBackoff(delay=5).context():
        source = urlopen(url)

    soup = BeautifulSoup(source, "html.parser")
    shelves_div = soup.find("div", {"id": "shelves"})
    shelf_links = shelves_div.findChildren("a")  # type: ignore
    futures = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        for link in shelf_links:
            base_url = link.attrs.get("href")
            shelf_name: str = re.search(r"\?shelf=([^&]+)", base_url)[1]
            if cli_args.get("include_shelves") is not None and shelf_name not in cli_args["include_shelves"]:
                logger.info(f"Skipping shelf (not in included shelves)'{shelf_name}'")
                continue
            if shelf_name in cli_args.get("exclude_shelves", []):
                logger.info(f"Skipping shelf (explicitly excluded) '{shelf_name}'")
                continue
            logger.info(f"Adding shelf '{shelf_name}' to thread pool.")
            futures.append(executor.submit(gr_shelves.get_shelf, cli_args, shelf_name))

    for future in as_completed(futures):
        shelf = future.result()
        for book_proc_dto in shelf:
            scrape_book_queue.put(book_proc_dto)

    logger.info("Finished getting all shelves")


def scrape_book_info(cli_args: argparse.Namespace[], queue: Queue, dlq: Queue) -> None:
    """
    Process 2: Takes items from the queue and processes each book's data.

    Args:
        cli_args (Dict[str, Any]): A dictionary containing configuration arguments. Key includes output_dir.
        queue (Queue): A queue containing books to be processed.
        dlq (Queue): A dead letter queue for storing books that failed during processing.

    This function continues running until it receives a sentinel (None) in the queue.
    """

    logger.info("Starting process_book worker")
    while True:
        process_book_args = queue.get()
        if process_book_args is None:
            logger.debug("Received sentinel, exiting")
            break  # Stop the loop if None is received, exit process

        book_file_path = os.path.join(args["output_dir"], f"{process_book_args['id']}.json")
        with GenericCache(book_file_path) as cache:
            book = cache.get(book_file_path)
            if book is not None:
                logger.info(f"[CACHED] {process_book_args['id']}")
            else:
                try:
                    book = scrape_book(process_book_args["id"], args)
                    logger.info(f"[SCRAPING] {process_book_args['id']}")
                    cache.set(book_file_path, book)
                except Exception as e:
                    logger.warning(f"Error scraping book {process_book_args['id']}", exc_info=True)
                    dlq.put((process_book_args, e))
                    continue
                finally:
                    if book is not None:
                        BookInfo.model_validate(book)

    logger.info("Finished processing all books")


def dump_queue(queue) -> list[dict]:
    """
    Empties all pending items in a queue and returns them in a list.
    """
    result = list(iter(queue.get, None))
    # not necessary but releases the GIL
    time.sleep(0.1)
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

    # for now we will just skip the shelves we don't want and hardcode this for my use case
    parser.add_argument("--include_shelves", type=bool, default=['favorites', 'read'])
    # parser.add_argument("--exclude_shelves", type=list, default=[])
    parser.add_argument(
        "--exclude_shelves",
        type=str,
        default=["hard-replacements", "guilty-pleasures"],
    )
    parser.add_argument("--skip_shelves", type=bool, default=False)
    parser.add_argument("--skip_authors", type=bool, default=False)
    parser.add_argument("--max_pages", type=bool, default=None)

    args = parser.parse_args()
    book_proc_workers = []
    num_process_book_workers = 5
    book_proc_queue: multiprocessing.Queue = multiprocessing.Queue()
    dlq: multiprocessing.Queue = multiprocessing.Queue()

    # Create the process book workers.  These will process books from the queue
    # and scrape the good reads data.  We start this first because we want this
    # running in the background picking up jobs as we add them to the queue
    for _ in range(num_process_book_workers):
        p = multiprocessing.Process(
            target=scrape_book_info, args=(args, book_proc_queue, dlq)
        )
        book_proc_workers.append(p)
        p.start()

    with Timer():
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
            logger.info(f"Directory '{args.output_dir}' was created.")
        else:
            logger.info(f"Directory '{args.output_dir}' already exists.")

        # Creating construct_library worker book_proc_workers
        p = multiprocessing.Process(
            target=construct_library, args=(args, book_proc_queue)
        )
        # book_proc_workers.append(p)
        p.start()
        p.join()
        logger.info("Finished getting all shelves adding sentinels")
        for _ in range(num_process_book_workers):
            #  we have to put a sentinel for each process book worker
            # if these dont match then a process will hang. We also do this here because
            # we have p.joined above and want to make sure we add these sentinels to
            # the very end of the queue
            book_proc_queue.put(None)

        # Wait for all book_proc_workers to complete
        logger.info("Waiting for all book_proc_workers to complete")
        for p in book_proc_workers:
            p.join()
        # Add a sentinel to the dead letter queue
        dlq.put(None)

    logger.info("Finished processing all books")

    # failures = dump_queue(dlq)
    # logger.warning(
    #     "The following could not be processed", len([f[0] for f in failures])
    # )
    # with open("failures.json", "w") as failures_file:
    #     json.dump({"failed_book_ids": failures}, failures_file, indent=2)

    # finalize_data = dict_merg

    # Signal process 2 to stop
    # book_proc_queue.put(None)
