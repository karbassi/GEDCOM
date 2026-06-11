"""Enable ``python -m gedcom7`` as an alias for the ``gedcom7`` CLI."""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
