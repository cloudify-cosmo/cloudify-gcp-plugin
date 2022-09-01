import os
import re

if __name__ == "__main__":
    branch = re.compile("[0-9.]*-build")
    if not branch.match(os.environ['CIRCLE_BRANCH']):
        raise ValueError("This is not build branch! Can't merge to the master.")