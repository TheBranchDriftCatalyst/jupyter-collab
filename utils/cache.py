import threading
import pickle
import os
from functools import wraps


def cache_decorator(key_getter=None, filename=None):
    def decorator(func):
        cache = {}
        lock = threading.Lock()

        # Load existing cache from file if filename is provided
        if filename and os.path.exists(filename):
            with open(filename, 'rb') as file:
                cache = pickle.load(file)

        @wraps(func)
        def wrapper(*args, **kwargs):
            if key_getter:
                key = key_getter(*args, **kwargs)
            else:
                key = (args, frozenset(kwargs.items()))

            with lock:
                if key not in cache:
                    cache[key] = func(*args, **kwargs)
                    # Save updated cache to file
                    if filename:
                        with open(filename, 'wb') as c_file:
                            pickle.dump(cache, c_file)

            return cache[key]

        return wrapper

    return decorator

# # Usage examples
# @cache_decorator(filename='square_cache.pkl')
# def compute_square(x):
#     return x * x
#
# @cache_decorator(key_getter=lambda x: x, filename='cube_cache.pkl')
# def compute_cube(x):
#     return x * x * x
#
# # Using the decorators
# result1 = compute_square(4)  # Computed and cached
# result2 = compute_square(4)  # Retrieved from cache or file
#
# result3 = compute_cube(3)    # Computed and cached
# result4 = compute_cube(3)    # Retrieved from cache or file
