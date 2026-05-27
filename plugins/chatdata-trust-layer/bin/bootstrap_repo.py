#!/usr/bin/env python3
import argparse
import shutil
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap a ChatData trust-layer repo from the plugin template.")
    parser.add_argument("target", help="Directory to create")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing directory")
    args = parser.parse_args()

    plugin_root = Path(__file__).resolve().parent.parent
    template_root = plugin_root / "assets" / "template-repo"
    target = Path(args.target).expanduser().resolve()

    if target.exists():
        if not args.force:
            print(f"Target already exists: {target}", file=sys.stderr)
            return 1
        shutil.rmtree(target)

    shutil.copytree(template_root, target)
    print(f"Bootstrapped ChatData trust-layer repo at {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
