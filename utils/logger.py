import logging
import os
import sys


cwd = os.getcwd()
repo_root = os.path.abspath(os.path.join(cwd, "../"))
sys.path.append(repo_root)
print(repo_root)

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
