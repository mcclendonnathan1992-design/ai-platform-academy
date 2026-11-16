"""Small toolkit for checking the files you write in labs/.

Checks are deliberately simple: they look at the structure of YOUR files
(resource types, parameters, hardening settings) and, when the real tool is
installed (terraform, docker, az/bicep), also run it. Nothing here deploys
anything or talks to Azure.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------- results


@dataclass
class Result:
    desc: str
    ok: bool | None  # None = skipped (tool not installed)
    detail: str = ""


class Ctx:
    """The folder with the learner's files."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def files(self, *patterns: str) -> list[Path]:
        found: list[Path] = []
        for pattern in patterns:
            found += sorted(p for p in self.root.glob(pattern) if p.is_file())
        return found

    def text(self, *patterns: str) -> str:
        return "\n".join(p.read_text(errors="replace") for p in self.files(*patterns))

    def exists(self, pattern: str) -> bool:
        return bool(self.files(pattern))


Check = Callable[[Ctx], Result]


def check(desc: str, fn: Callable[[Ctx], bool | str]) -> Check:
    """Wrap a predicate. Return True for pass, or a string to explain a failure."""

    def run(ctx: Ctx) -> Result:
        try:
            outcome = fn(ctx)
        except Exception as exc:  # noqa: BLE001 - a broken file is a failed check
            return Result(desc, False, f"{type(exc).__name__}: {exc}")
        if outcome is True:
            return Result(desc, True)
        return Result(desc, False, outcome if isinstance(outcome, str) else "")

    return run


def run_tool(desc: str, tool: str, args: list[str], cwd: Path, timeout: int = 180) -> Result:
    if os.environ.get("LABKIT_NO_TOOLS"):
        return Result(desc, None, "tool checks disabled")
    if shutil.which(tool) is None:
        return Result(desc, None, f"{tool} not installed here (runs in your Codespace)")
    try:
        p = subprocess.run([tool, *args], cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return Result(desc, False, "timed out")
    return Result(desc, p.returncode == 0, (p.stdout + p.stderr).strip()[-400:] if p.returncode else "")


# ---------------------------------------------------------------- brace blocks (HCL and Bicep)


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"(^|\s)(#|//).*", r"\1", text)


def _match_brace(text: str, start: int) -> int:
    depth, i, in_str = 0, start, None
    while i < len(text):
        ch = text[i]
        if in_str:
            if ch == "\\":
                i += 1
            elif ch == in_str:
                in_str = None
        elif ch in "\"'":
            in_str = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced braces")


@dataclass
class Block:
    kind: str
    labels: tuple[str, ...]
    body: str


_TF_HEAD = re.compile(r'^\s*(resource|data|variable|output|module|provider|terraform|locals)\b((?:\s+"[^"]*")*)\s*\{', re.M)
_BICEP_HEAD = re.compile(r"^\s*(resource|module)\s+(\w+)\s+'([^']+)'(?:\s+existing)?\s*=\s*(?:if\s*\([^)]*\)\s*)?(?:\[\s*for\b[^{]*)?\{", re.M)


def tf_blocks(text: str) -> list[Block]:
    text = strip_comments(text)
    blocks = []
    for m in _TF_HEAD.finditer(text):
        end = _match_brace(text, m.end() - 1)
        labels = tuple(re.findall(r'"([^"]*)"', m.group(2)))
        blocks.append(Block(m.group(1), labels, text[m.end() : end]))
    return blocks


def bicep_blocks(text: str) -> list[Block]:
    text = strip_comments(text)
    blocks = []
    for m in _BICEP_HEAD.finditer(text):
        end = _match_brace(text, m.end() - 1)
        blocks.append(Block(m.group(1), (m.group(2), m.group(3)), text[m.end() : end]))
    return blocks


# ---------------------------------------------------------------- Terraform helpers


def tf_text(ctx: Ctx) -> str:
    return ctx.text("*.tf", "**/*.tf")


def tf_has_resource(ctx: Ctx, rtype: str) -> bool:
    return any(b.kind == "resource" and b.labels[:1] == (rtype,) for b in tf_blocks(tf_text(ctx)))


def tf_resource_body(ctx: Ctx, rtype: str) -> str:
    return "\n".join(b.body for b in tf_blocks(tf_text(ctx)) if b.kind == "resource" and b.labels[:1] == (rtype,))


def tf_resource_has(ctx: Ctx, rtype: str, pattern: str) -> bool | str:
    body = tf_resource_body(ctx, rtype)
    if not body:
        return f'no resource "{rtype}" found'
    return True if re.search(pattern, body, re.S) else f'resource "{rtype}" is missing /{pattern}/'


def tf_declares(ctx: Ctx, kind: str, name: str) -> bool:
    return any(b.kind == kind and b.labels[:1] == (name,) for b in tf_blocks(tf_text(ctx)))


def tf_syntax(ctx: Ctx) -> bool | str:
    import hcl2  # python-hcl2

    files = ctx.files("*.tf", "**/*.tf")
    if not files:
        return "no .tf files"
    for f in files:
        with f.open() as fh:
            hcl2.load(fh)
    return True


# ---------------------------------------------------------------- Bicep helpers


def bicep_text(ctx: Ctx) -> str:
    return strip_comments(ctx.text("*.bicep", "**/*.bicep"))


def bicep_has_resource(ctx: Ctx, rtype_prefix: str) -> bool:
    return any(b.kind == "resource" and b.labels[1].lower().startswith(rtype_prefix.lower() + "@") for b in bicep_blocks(bicep_text(ctx)))


def bicep_resource_has(ctx: Ctx, rtype_prefix: str, pattern: str) -> bool | str:
    bodies = [b.body for b in bicep_blocks(bicep_text(ctx)) if b.kind == "resource" and b.labels[1].lower().startswith(rtype_prefix.lower() + "@")]
    if not bodies:
        return f"no resource of type {rtype_prefix}"
    return True if any(re.search(pattern, body, re.S) for body in bodies) else f"{rtype_prefix} is missing /{pattern}/"


def bicep_tool(ctx: Ctx) -> Result:
    """Compile every .bicep with whatever is installed."""
    files = ctx.files("*.bicep", "**/*.bicep")
    if not files:
        return Result("bicep compiles", False, "no .bicep files")
    if os.environ.get("LABKIT_NO_TOOLS"):
        return Result("bicep compiles", None, "tool checks disabled")
    for tool, prefix in (("bicep", []), ("az", ["bicep"])):
        if shutil.which(tool):
            for f in files:
                res = run_tool("bicep compiles", tool, [*prefix, "build", "--stdout", str(f)], ctx.root)
                if not res.ok:
                    return Result("bicep compiles", False, f"{f.name}: {res.detail}")
            return Result("bicep compiles", True)
    return Result("bicep compiles", None, "bicep/az not installed here (runs in your Codespace)")


# ---------------------------------------------------------------- JSON / YAML / Docker helpers


def load_json(path: Path):
    return json.loads(path.read_text())


def load_yaml_docs(ctx: Ctx, *patterns: str) -> list[dict]:
    import yaml

    docs: list[dict] = []
    for f in ctx.files(*patterns):
        docs += [d for d in yaml.safe_load_all(f.read_text()) if isinstance(d, dict)]
    return docs


def dockerfile_instructions(path: Path) -> list[tuple[str, str]]:
    """[(INSTRUCTION, args)] with line continuations joined and comments removed."""
    out: list[tuple[str, str]] = []
    buf = ""
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith("\\"):
            buf += line[:-1] + " "
            continue
        line = buf + line
        buf = ""
        name, _, args = line.partition(" ")
        out.append((name.upper(), args.strip()))
    return out


# ---------------------------------------------------------------- runner


def run_checks(checks: list[Check], ctx: Ctx) -> list[Result]:
    return [c(ctx) for c in checks]


def passed(results: list[Result]) -> bool:
    return all(r.ok in (True, None) for r in results)


def terraform_tool(ctx: Ctx) -> list[Result]:
    """fmt -check, then init (no backend) + validate, if terraform is installed."""
    out = [run_tool("terraform fmt is clean", "terraform", ["fmt", "-check", "-recursive"], ctx.root)]
    init = run_tool("terraform init", "terraform", ["init", "-backend=false", "-input=false"], ctx.root, timeout=300)
    if init.ok is None:
        out.append(Result("terraform validate", None, init.detail))
    elif not init.ok:
        out.append(Result("terraform validate", False, "init failed: " + init.detail))
    else:
        out.append(run_tool("terraform validate", "terraform", ["validate"], ctx.root))
    return out


GUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
