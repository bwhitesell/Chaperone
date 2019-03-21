import os
import sys

import commands


if __name__ == "__main__":
    # check for arguments
    if len(sys.argv) < 2:
        raise ValueError("No command provided.")
    try:
        getattr(commands, sys.argv[1])()
    except AttributeError:
        raise ValueError("{sys.argv[1]} is not a valid command. Check for typos.")