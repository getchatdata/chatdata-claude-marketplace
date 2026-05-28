#!/usr/bin/env python3
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    metric_count = len(list((root / "metrics").glob("*.yaml")))
    answer_path_count = len(list((root / "answer-paths").glob("*.yaml")))
    print(f"Metrics tracked: {metric_count}")
    print(f"Answer paths tracked: {answer_path_count}")
    print("Drift review is still a human-in-the-loop step in v1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
