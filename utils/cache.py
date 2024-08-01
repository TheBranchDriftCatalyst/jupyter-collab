import threading
import os
import functools
import json
import pickle


class GenericCache:
    def __init__(self, filename):
        self.filename = filename
        self.cache = {}
        self.lock = threading.Lock()

        # Infer serialization type from file extension
        _, file_extension = os.path.splitext(filename)
        if file_extension in ['.pkl', '.pickle']:
            self.serialization_type = 'pickle'
        elif file_extension in ['.json']:
            self.serialization_type = 'json'
        else:
            raise ValueError("Unsupported file type. Please use .pkl, .pickle, or .json")

        self._load_cache()

    def _load_cache(self) -> None
        if os.path.exists(self.filename):
            with open(self.filename, 'rb' if self.serialization_type == 'pickle' else 'r') as file:
                self.cache = self._deserialize(file)


    def _serialize(self, file) -> None:
        if self.serialization_type == 'pickle':
            pickle.dump(self.cache, file)
        elif self.serialization_type == 'json':
            json.dump(self.cache, file, indent=2)

    def _deserialize(self, file) -> dict
        if self.serialization_type == 'pickle':
            return pickle.load(file)
        elif self.serialization_type == 'json':
            return json.load(file)
        return {}

    def _write_cache(self) -> None:
        with open(self.filename, 'wb' if self.serialization_type == 'pickle' else 'w') as file:
            self._serialize(file)

    def __call__(self, func, key_getter=None) -> callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = key_getter(*args, **kwargs) if key_getter else (args, frozenset(kwargs.items()))

            with self.lock:
                if key not in self.cache:
                    self.cache[key] = func(*args, **kwargs)
                    self._write_cache()
            return self.cache[key]
        return wrapper

    def __enter__(self):
        return self

    def get(self, key):
        return self.cache.get(key, None)

    def set(self, key, value):
        with self.lock:
            self.cache[key] = value
            self._write_cache()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Any cleanup if needed when exiting the context
        pass  # Cache is saved in set, so no action needed here

# # Usage as decorator with pickle serialization:
# @GenericCache('square_cache.pkl')
# def compute_square(x):
#     return x * x
#
# # Usage as context manager with json serialization:
# with GenericCache('generic_cache.json') as cache:
#     book = cache.get('some_key')
#     if book is None:
#         book = "data from scrape_book or other sources"
#         cache.set('some_key', book)
