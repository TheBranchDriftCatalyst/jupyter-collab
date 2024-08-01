import os
import sys

cwd = os.getcwd()
repo_root = os.path.abspath(os.path.join(cwd, "../.."))
sys.path.append(repo_root)
print(repo_root)
