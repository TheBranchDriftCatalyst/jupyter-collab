import pickle
import logging
import hashlib

# dont use this one, use the cache decorator instead


class RequestCache:

    def __init__(self, filename):
        self.filename = filename
        self.cache = self.load()

    def load(self):
        try:
            with open(self.filename, "rb") as f:
                cache = pickle.load(f)
            logging.info(f"Cache loaded from {self.filename}")
        except FileNotFoundError:
            logging.info(
                f"No cache file found at {self.filename}. Creating a new cache."
            )
            cache = {}
        except EOFError:
            logging.warning(
                f"Empty or corrupted cache file at {self.filename}. Creating a new cache."
            )
            cache = {}
        return cache

    def save(self):
        with open(self.filename, "wb") as f:
            pickle.dump(self.cache, f)
        logging.info(f"Cache saved to {self.filename}")

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        self.cache[key] = value

    @staticmethod
    def generate_key(chunk):
        return hashlib.sha256(chunk.encode("utf-8")).hexdigest()
