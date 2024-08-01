import pytest
from dotenv import load_dotenv
import os

# Not necessary since we are using a .env ---> .envrc pattern
# @pytest.fixture(scope='session', autouse=True)
# def load_env() -> None:
#     print("Loading ENV")
#     # Assuming .envrc is in the project root
#     if not load_dotenv('./.env', verbose=True, override=True):
#         raise EnvironmentError("Could not load .envrc file")
