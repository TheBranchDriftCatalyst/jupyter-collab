import time
import random
import functools
import contextlib

class ExpoBackoff:
    def __init__(self, delay=10, backoff_factor=2, max_attempts=5, jitter=None, on_error=Exception):
        self.delay = delay
        self.backoff_factor = backoff_factor
        self.max_attempts = max_attempts
        self.jitter = jitter or (lambda: random.uniform(0, self.delay / 2))
        self.on_error = on_error

    @contextlib.contextmanager
    def context(self):
        attempt = 0
        while attempt < self.max_attempts:
            try:
                yield
                break
            except self.on_error:
                attempt += 1
                sleep_time = self.delay * (self.backoff_factor ** attempt)
                sleep_time += self.jitter()
                time.sleep(sleep_time)

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self.context():
                return func(*args, **kwargs)
        return wrapper

# # Usage as a context manager
# with ExpoBackoff(delay=1, max_attempts=3, on_error=ValueError).context() as backoff:
#     # Code that might throw a ValueError


# # Usage as a decorator
# @ExpoBackoff(delay=1, max_attempts=3, on_error=ValueError)
# def some_function():
#     # Function implementation
