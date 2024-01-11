import contextlib
import time
import random
import functools
import logging

logger = logging.getLogger(__name__)

class ExpoBackoff:
    def __init__(self, delay=20, backoff_factor=2, max_attempts=5, jitter=None, on_error=Exception):
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
                return  # Make sure to return after successful execution
            except self.on_error as e:
                attempt += 1
                if attempt >= self.max_attempts:
                    logger.error(f"Max attempts reached. Last error: {e}")
                    raise  # Re-raise the exception to propagate the error
                logger.warning(f"Error occurred. Retrying in {self.delay} seconds. attempt={attempt} of {self.max_attempts}")
                logger.error("Error occurred", exc_info=True)
                sleep_time = self.delay * (self.backoff_factor ** attempt)
                sleep_time += self.jitter()
                time.sleep(sleep_time)
        # Log if exited loop without success
        logger.error("Exited retry loop without success. This might be unexpected.")

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self.context():
                return func(*args, **kwargs)
        return wrapper
