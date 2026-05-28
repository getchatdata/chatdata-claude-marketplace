#!/usr/bin/env python3
from pathlib import Path
import sys


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    required = [
        root / "metrics",
        root / "answer-paths",
        root / "queries" / "trusted",
        root / "queries" / "generated",
        root / "artifacts",
        root / "evals",
        root / "catalog",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        for path in missing:
            print(f"Missing required path: {path}", file=sys.stderr)
        return 1
    print("Trust-layer template looks structurally valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
