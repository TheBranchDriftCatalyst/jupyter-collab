import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# from multiprocessing import Queue
import queue

import os

import sys
import logging


cwd = os.getcwd()
repo_root = os.path.abspath(os.path.join(cwd, "../"))
sys.path.append(repo_root)
print(repo_root)

from goodreads_scraper import shelves
from goodreads_scraper import user
from goodreads_scraper import books

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# # Create a file handler
# log_file = "scrapper.log"
# if os.path.exists(log_file):
#     os.remove(log_file)

# # file_handler = logging.FileHandler(log_file, mode="w")
# # file_handler.setLevel(level=logging.DEBUG)

# # Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# # Create a formatter and set it for both handlers
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
# # file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# # Add the handlers to the logger
# # logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.debug(f"This is a debug message - {os.getcwd()}")


def scrape_user(args: argparse.Namespace):
    user.get_user_info(args)
    shelves.get_all_shelves(args)


def main():
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

    args = parser.parse_args()

    # args.output_dir = (
    #     args.output_dir if args.output_dir.endswith("/") else args.output_dir + "/"
    # )

    # os.makedirs(args.output_dir, exist_ok=True)

    book_list = set()
    shelf_mapping_data = []
    futures = shelves.get_all_shelves_threaded(
        args,
        exclude_shelves=["to-read"],
    )
    # logger.info(f"Shelves futures: {futures}")
    for future in as_completed(futures):
        books_on_shelf, book_shelf_mapping_data_part = future.result()
        books_on_shelf = set(books_on_shelf)
        shelf_mapping_data.append(book_shelf_mapping_data_part)

    merged_books = defaultdict(list)

    print()
    
    # for book in list(book_list):
    #     print(book)
    #     for key, value in book.items():
    #         merged_books[key].extend(value)
    
    # with open(f"{args.output_dir}/merged_books.json", "w") as file:
    #     json.dump(merged_books, fp=file, indent=2)

    # num_threads = 5  # Adjust as needed

    # book_futures = []
    # with ThreadPoolExecutor(max_workers=num_threads) as executor:
    #     # Submit tasks to the executor
    #     for book_id in books_queue.queue:
    #         logger.info(f"Adding book '{book_id}' to thread pool.")
    #         bf = executor.submit(books.scrape_book, book_id, args)
    #         book_futures.append(bf)

    #     try:
    #         result = future.result()
    #         with open(f"./output/{result['id']}", "w") as file:
    #             json.dump(result, fp=file, indent=2)
    #             # storyProcessBar.set_description(
    #             #     f"Processed {result.get('title', 'UNKNOWN'):<30}"
    #             # )
    #             # storyProcessBar.update()
    #     except Exception as e:
    #         logger.error(
    #             "something got fucked up",
    #             e
    #             # f"Processing of story {title} at {url} raised an exception: {e}"
    #         )


if __name__ == "__main__":
    main()
