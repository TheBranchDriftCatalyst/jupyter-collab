from contextlib import contextmanager
import threading

lock = threading.Lock()

@contextmanager
def generic_context_manager(resource_creator):
    lock.acquire()
    resource = None
    try:
        resource = resource_creator()
        yield resource
    finally:
        if hasattr(resource, 'close'):
            resource.close()
        lock.release()

# Usage examples
# filename = 'example.txt'

# # Using with a file
# with generic_context_manager(lambda: open(filename, 'a')) as file:
#     file.write('Some data\n')
#
# # Using with a different type of resource (e.g., a dictionary)
# with generic_context_manager(lambda: {}) as my_dict:
#     my_dict['key'] = 'value'
#     # Do something with the dictionary
