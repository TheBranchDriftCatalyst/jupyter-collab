import time
import functools
from logging import getLogger

logger = getLogger(__name__)

logger.setLevel("DEBUG")


class Timer:
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start
        logger.info(f"Elapsed time: {self.interval:.2f} seconds")

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper

# # Usage as a context manager
# with Timer():
#     # Code block to time

# # Usage as a decorator
# @Timer()
# def some_function():
#     # Function implementation
