from __future__ import annotations

import importlib
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent / "src"))


def main() -> int:
    module = importlib.import_module("md2ipynb.cli")
    return module.main()


if __name__ == "__main__":
    raise SystemExit(main())
