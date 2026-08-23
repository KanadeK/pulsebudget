from __future__ import annotations

import argparse
from collections.abc import Sequence

from pulsebudget import __version__


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pulsebudget",
        description="Explain and gate embedded current-trace regressions.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.parse_args(argv)
    return 0

