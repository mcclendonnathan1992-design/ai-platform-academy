"""Golden-path scaffold: python scripts/new_service.py my-service [--dest DIR]

Copies platform/golden-path/template, replacing __NAME__ with the service name.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "platform" / "golden-path" / "template"
DNS_1123 = re.compile(r"^[a-z0-9]([-a-z0-9]{0,61}[a-z0-9])?$")


def scaffold(name: str, dest: Path, template: Path = TEMPLATE) -> Path:
    if not DNS_1123.match(name):
        raise ValueError(f"{name!r} is not a valid Kubernetes name (lowercase letters, digits, '-').")
    target = dest / name
    if target.exists():
        raise FileExistsError(f"{target} already exists.")
    shutil.copytree(template, target)
    for path in target.rglob("*"):
        if path.is_file():
            path.write_text(path.read_text().replace("__NAME__", name))
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("--dest", default=".", type=Path)
    args = parser.parse_args(argv)
    try:
        target = scaffold(args.name, args.dest)
    except (ValueError, FileExistsError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Created {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
