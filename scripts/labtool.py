"""Reset a lab, or plant fresh bugs in it so you can drill the same lab again.

    python scripts/labtool.py reset 05      # archive your work, restore a blank work/
    python scripts/labtool.py break 05      # copy the solution into work/ with 3 hidden bugs
    python scripts/labtool.py break 05 --seed 7 --bugs 2
    python scripts/labtool.py reveal 05     # show which bugs were planted (give up, or check yourself)

Nothing is ever deleted: `reset` and `break` move what was in work/ to .attempts/ first.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
ATTEMPTS = ROOT / ".attempts"

from lab_check import run_lab  # noqa: E402
from lab_specs import LABS  # noqa: E402

# ---------------------------------------------------------------- the bugs we can plant

Mutation = tuple[str, Callable[[str], "str | None"]]  # (what it is, text -> new text or None if not applicable)


def sub(pattern: str, repl: str, flags: int = 0) -> Callable[[str], "str | None"]:
    def run(text: str) -> "str | None":
        new, n = re.subn(pattern, repl, text, count=1, flags=flags)
        return new if n else None

    return run


def flip(key: str, old: str, new: str) -> Mutation:
    return (f"{key} changed from {old} to {new}", sub(rf"(\b{key}\s*[=:]\s*){re.escape(old)}", rf"\g<1>{new}"))


DOCKERFILE: list[Mutation] = [
    ("base image unpinned (:latest)", sub(r"^(FROM\s+[^\s:]+):[^\s]+", r"\1:latest", re.M)),
    ("USER instruction removed (runs as root)", sub(r"^USER .*\n", "", re.M)),
    ("CMD changed from exec form to shell form", sub(r'^CMD \["([^"]+)"(?:,\s*"([^"]+)")?\]', lambda m: None, re.M)),  # replaced below
    ("HEALTHCHECK removed", sub(r"^HEALTHCHECK .*\n", "", re.M)),
    ("EXPOSE removed", sub(r"^EXPOSE .*\n", "", re.M)),
    ("ADD from a remote URL", sub(r"^(WORKDIR .*\n)", r"\1ADD https://example.com/tool.tar.gz /opt/\n", re.M)),
]


def _cmd_to_shell(text: str) -> "str | None":
    m = re.search(r"^CMD \[(.*)\]\s*$", text, re.M)
    if not m:
        return None
    words = " ".join(w.strip().strip('"') for w in m.group(1).split(","))
    return text[: m.start()] + f"CMD {words}" + text[m.end():]


DOCKERFILE[2] = ("CMD changed from exec form to shell form", _cmd_to_shell)

TERRAFORM: list[Mutation] = [
    ("subscription_id line removed from the provider", sub(r"^\s*subscription_id\s*=\s*var\.subscription_id\s*\n", "", re.M)),
    ("subscription id hardcoded instead of a variable", sub(r"subscription_id\s*=\s*var\.subscription_id", 'subscription_id = "00000000-0000-0000-0000-000000000001"')),
    ("azurerm provider version loosened", sub(r'"~> 4\.0"', '">= 3.0"')),
    ("NSG deny rule moved to priority 100", sub(r"priority(\s*)=(\s*)4096", r"priority\1=\g<2>100")),
    flip("private_cluster_enabled", "true", "false"),
    flip("local_account_disabled", "true", "false"),
    flip("azure_rbac_enabled", "true", "false"),
    flip("admin_enabled", "false", "true"),
    flip("https_traffic_only_enabled", "true", "false"),
    flip("allow_nested_items_to_be_public", "false", "true"),
    ("required_version removed", sub(r"^\s*required_version\s*=.*\n", "", re.M)),
    ("a provider version pin removed", sub(r"\n\s*version\s*=\s*\"~> [\d.]+\"", "")),
    ("a description removed", sub(r"\n\s*description\s*=\s*\"[^\"]*\"", "")),
    ("for_each replaced by count", sub(r"for_each(\s*)=(\s*)var\.(\w+)", r"count\1=\2length(var.\3)")),
]

BICEP: list[Mutation] = [
    flip("supportsHttpsTrafficOnly", "true", "false"),
    flip("allowBlobPublicAccess", "false", "true"),
    flip("disableLocalAccounts", "true", "false"),
    flip("enablePrivateCluster", "true", "false"),
    flip("enableAzureRBAC", "true", "false"),
    flip("adminUserEnabled", "false", "true"),
    ("minimum TLS version lowered", sub(r"minimumTlsVersion:\s*'TLS1_2'", "minimumTlsVersion: 'TLS1_0'")),
    ("public network access enabled", sub(r"publicNetworkAccess:\s*'Disabled'", "publicNetworkAccess: 'Enabled'")),
    ("NSG deny rule moved to priority 100", sub(r"priority:\s*4096", "priority: 100")),
    ("module output renamed", sub(r"^(\s*output\s+)id(\s)", r"\1resourceId\2", re.M)),
]

SHELL: list[Mutation] = [
    ("--parameters @parameters.json dropped from a command", sub(r"\s*--parameters @parameters\.json", "")),
]


def _json_inline_secret(text: str) -> "str | None":
    data = json.loads(text)
    for param in data.get("parameters", {}).values():
        if isinstance(param, dict) and "reference" in param:
            param.clear()
            param["value"] = "ChangeMe-123!"
            return json.dumps(data, indent=2) + "\n"
    return None


def _json_drop_schema(text: str) -> "str | None":
    data = json.loads(text)
    return json.dumps({k: v for k, v in data.items() if k != "$schema"}, indent=2) + "\n" if "$schema" in data else None


JSON: list[Mutation] = [
    ("secret stored as a plain value instead of a Key Vault reference", _json_inline_secret),
    ("$schema removed", _json_drop_schema),
]

KUBERNETES: list[Mutation] = [
    flip("runAsNonRoot", "true", "false"),
    flip("allowPrivilegeEscalation", "false", "true"),
    flip("readOnlyRootFilesystem", "true", "false"),
    ("image tag changed to :latest", sub(r"(\bimage:\s*[^\s:]+):[^\s]+", r"\1:latest")),
    ("Service selector no longer matches the pods", sub(r"(selector:\s*\n\s+app(?:\.kubernetes\.io/name)?:\s*)(\S+)", r"\g<1>\2-typo")),
]

COMPOSE: list[Mutation] = [
    ("depends_on waits only for start, not health", sub(r"condition:\s*service_healthy", "condition: service_started")),
    ("redis image unpinned (:latest)", sub(r"(\bimage:\s*redis):[^\s]+", r"\1:latest")),
]


def mutations_for(path: Path) -> list[Mutation]:
    name = path.name
    if name == "Dockerfile":
        return DOCKERFILE
    if path.suffix == ".tf":
        return TERRAFORM
    if path.suffix == ".bicep":
        return BICEP
    if path.suffix == ".sh":
        return SHELL
    if path.suffix == ".json":
        return JSON
    if name in ("docker-compose.yml", "docker-compose.yaml"):
        return COMPOSE
    if path.suffix in (".yml", ".yaml"):
        return KUBERNETES
    return []


# ---------------------------------------------------------------- helpers


def lab_dirs(lab: str) -> tuple[str, Path]:
    lab = lab.zfill(2)
    if lab not in LABS:
        sys.exit(f"No lab {lab!r}. Choose from: {', '.join(LABS)}")
    return lab, ROOT / "labs" / LABS[lab][0]


def real_files(folder: Path) -> list[Path]:
    return [p for p in folder.rglob("*") if p.is_file() and p.name != ".gitkeep"]


def archive_work(lab: str, work: Path) -> Path | None:
    """Move whatever is in work/ to .attempts/ so nothing is ever lost."""
    items = [p for p in work.iterdir() if p.name != ".gitkeep"] if work.exists() else []
    if not items:
        return None
    dest = ATTEMPTS / f"{lab}-{time.strftime('%Y%m%d-%H%M%S')}"
    dest.mkdir(parents=True, exist_ok=True)
    for p in items:
        shutil.move(str(p), dest / p.name)
    return dest


def fill_work(*sources: Path, work: Path) -> None:
    """Copy each source folder into work/ in order (later ones overwrite earlier ones)."""
    work.mkdir(parents=True, exist_ok=True)
    for src in sources:
        if not src.exists():
            continue
        for p in src.iterdir():
            target = work / p.name
            if p.is_dir():
                shutil.copytree(p, target, dirs_exist_ok=True)
            else:
                shutil.copy2(p, target)
    (work / ".gitkeep").touch()


def failures(lab: str) -> int:
    """How many structural checks fail right now (external tools are off so this is fast and offline)."""
    old = os.environ.get("LABKIT_NO_TOOLS")
    os.environ["LABKIT_NO_TOOLS"] = "1"
    try:
        return sum(1 for r in run_lab(lab, "work") if r.ok is False)
    finally:
        if old is None:
            os.environ.pop("LABKIT_NO_TOOLS", None)
        else:
            os.environ["LABKIT_NO_TOOLS"] = old


# ---------------------------------------------------------------- commands


def cmd_reset(lab: str) -> int:
    lab, base = lab_dirs(lab)
    work, given = base / "work", base / "given"
    moved = archive_work(lab, work)
    work.mkdir(parents=True, exist_ok=True)
    (work / ".gitkeep").touch()
    if given.exists() and real_files(given):
        fill_work(given, work=work)
        print(f"Lab {lab}: work/ restored from given/ (the starting files).")
    else:
        print(f"Lab {lab}: work/ is blank again.")
    if moved:
        print(f"Your previous attempt is saved in {moved.relative_to(ROOT)}/")
    print(f"Start over: read labs/{base.name}/README.md, then  make lab-check LAB={lab}")
    return 0


def cmd_break(lab: str, bugs: int, seed: int | None) -> int:
    lab, base = lab_dirs(lab)
    solution, work = base / "solution", base / "work"
    if not solution.exists() or not real_files(solution):
        print(f"Lab {lab} has no reference solution to break (it is open-ended). Use: make reset-lab LAB={lab}")
        return 1
    seed = random.randrange(10_000) if seed is None else seed
    rng = random.Random(seed)
    moved = archive_work(lab, work)
    fill_work(base / "given", solution, work=work)
    candidates = [(f, m) for f in real_files(work) for m in mutations_for(f)]
    rng.shuffle(candidates)
    planted: list[dict[str, str]] = []
    for path, (what, fn) in candidates:
        if len(planted) >= bugs:
            break
        text = path.read_text()
        new = fn(text)
        if new is None or new == text:
            continue
        before = failures(lab)
        path.write_text(new)
        if failures(lab) > before:  # keep only bugs the checker can see
            planted.append({"file": str(path.relative_to(work)), "bug": what})
        else:
            path.write_text(text)
    if not planted:
        archive_work(lab, work)
        print(f"Could not plant a detectable bug in lab {lab}. Use: make reset-lab LAB={lab}")
        return 1
    ATTEMPTS.mkdir(exist_ok=True)
    (ATTEMPTS / f"bugs-{lab}.json").write_text(json.dumps({"seed": seed, "bugs": planted}, indent=2))
    print(f"Lab {lab}: planted {len(planted)} bug(s) in labs/{base.name}/work/ (seed {seed}).")
    print("Find them the way you would on the job: read, run the tools, think. Fix in place.")
    print(f"  make lab-check LAB={lab}     # fails until every bug is fixed")
    print(f"  make reveal LAB={lab}        # shows the answers when you want them")
    if moved:
        print(f"(Your previous work is saved in {moved.relative_to(ROOT)}/)")
    return 0


def cmd_reveal(lab: str) -> int:
    lab, _ = lab_dirs(lab)
    f = ATTEMPTS / f"bugs-{lab}.json"
    if not f.exists():
        print(f"No planted bugs recorded for lab {lab}. Run: make break-lab LAB={lab}")
        return 1
    data = json.loads(f.read_text())
    print(f"Lab {lab} bugs (seed {data['seed']}):")
    for b in data["bugs"]:
        print(f"  - {b['file']}: {b['bug']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="labtool")
    sub_ = ap.add_subparsers(dest="cmd", required=True)
    for name in ("reset", "break", "reveal"):
        p = sub_.add_parser(name)
        p.add_argument("lab")
        if name == "break":
            p.add_argument("--bugs", type=int, default=3)
            p.add_argument("--seed", type=int)
    args = ap.parse_args(argv)
    if args.cmd == "reset":
        return cmd_reset(args.lab)
    if args.cmd == "break":
        return cmd_break(args.lab, args.bugs, args.seed)
    return cmd_reveal(args.lab)


if __name__ == "__main__":
    raise SystemExit(main())
