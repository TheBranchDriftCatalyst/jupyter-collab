__version__ = "1.1.0"

import logging


def setup_logging():
    # Configure the root logger to log at DEBUG level
    # Include thread name in the log format
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')


# Call the setup function to configure logging at import
setup_logging()


logging.debug("This is a debug message")
logging.info("This is an info message")
logging.warning("This is a warning message")
logging.error("This is an error message")
logging.critical("This is a critical message")

