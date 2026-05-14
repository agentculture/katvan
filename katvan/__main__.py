"""Allow running katvan as ``python -m katvan``."""

import sys

from katvan.cli import main

if __name__ == "__main__":
    sys.exit(main())
