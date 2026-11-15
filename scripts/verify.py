"""Checkpoint for each module.  python scripts/verify.py 04   (or: make verify-04)

Each check prints PASS/FAIL with a hint. Exit code 0 only if all pass.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NS = os.environ.get("NAMESPACE", "ai-lab")
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
GATEWAY = os.environ.get("GATEWAY_URL", "http://localhost:8080")


def run(cmd: list[str], timeout: int = 60) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return 127, str(exc)
    return p.returncode, (p.stdout + p.stderr).strip()


def http_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as r:
        return json.load(r)


def have(tool: str) -> tuple[bool, str]:
    return shutil.which(tool) is not None, f"install {tool} (see modules/00-setup)"


def files_exist(*paths: str) -> tuple[bool, str]:
    missing = [p for p in paths if not (ROOT / p).exists()]
    return not missing, f"missing: {', '.join(missing)}" if missing else ""


def check_00() -> list[tuple[str, tuple[bool, str]]]:
    return [(f"{t} installed", have(t)) for t in ("git", "python3", "docker", "kubectl", "kind", "terraform", "helm", "ollama")]


def check_01() -> list:
    code, out = run([sys.executable, "-m", "pytest", "-q", "modules/01-design/sim"])
    return [("concept simulation tests pass", (code == 0, out[-300:])),
            ("traceability doc exists", files_exist("docs/design/traceability.md"))]


def check_02() -> list:
    def ollama_up() -> tuple[bool, str]:
        try:
            http_json(f"{OLLAMA}/api/tags")
            return True, ""
        except Exception as exc:  # noqa: BLE001
            return False, f"Ollama not reachable at {OLLAMA}: {exc}"

    def model_present() -> tuple[bool, str]:
        try:
            names = [m["name"] for m in http_json(f"{OLLAMA}/api/tags").get("models", [])]
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)
        return bool(names), "no models yet: ollama pull llama3.2:1b"

    return [("ollama reachable", ollama_up()), ("at least one model pulled", model_present())]


def check_03() -> list:
    def healthz() -> tuple[bool, str]:
        try:
            return http_json(f"{GATEWAY}/healthz").get("status") == "ok", ""
        except Exception as exc:  # noqa: BLE001
            return False, f"gateway not reachable at {GATEWAY}: {exc}"

    code, out = run(["docker", "image", "inspect", "ai-gateway:dev"])
    return [("image ai-gateway:dev built", (code == 0, "docker build -t ai-gateway:dev app")),
            ("gateway /healthz ok", healthz())]


def check_04() -> list:
    results = []
    for name in ("ollama", "gateway"):
        code, out = run(["kubectl", "-n", NS, "rollout", "status", f"deploy/{name}", "--timeout=5s"])
        results.append((f"deployment/{name} ready in {NS}", (code == 0, out[-200:])))
    return results


def check_05() -> list:
    code, out = run(["terraform", "-chdir=terraform/local", "validate"])
    return [("terraform/local validates (run terraform init first)", (code == 0, out[-300:]))]


def check_06() -> list:
    return [("CI + GitOps files present", files_exist(".github/workflows/ci.yml", ".github/workflows/image.yml", "gitops/argocd/application.yaml"))]


def check_07() -> list:
    results = [("RBAC + policy files present", files_exist("k8s/security/rbac.yaml", "k8s/security/kyverno-policies.yaml", "platform/golden-path/template/k8s/deployment.yaml"))]
    code, out = run(["kubectl", "auth", "can-i", "get", "pods", "-n", NS, "--as=jane", "--as-group=ai-developers"])
    results.append(("ai-developers can get pods", (out.strip().startswith("yes"), "kubectl apply -f k8s/security/rbac.yaml")))
    code, out = run(["kubectl", "auth", "can-i", "delete", "pods", "-n", NS, "--as=jane", "--as-group=ai-developers"])
    results.append(("ai-developers cannot delete pods", (out.strip().startswith("no"), "Role is too broad")))
    return results


def check_08() -> list:
    code, out = run([sys.executable, "-m", "pytest", "-q", "app/tests"])
    return [("gateway tests pass", (code == 0, out[-300:])), ("eval set present", files_exist("eval/golden.jsonl"))]


def check_09() -> list:
    return [("capstone write-up exists", files_exist("modules/09-capstone/CAPSTONE.md"))]


CHECKS = {f"{i:02d}": globals()[f"check_{i:02d}"] for i in range(10)}


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0].zfill(2) not in CHECKS:
        print(f"usage: verify.py <{'|'.join(CHECKS)}>")
        return 2
    failed = 0
    for label, (ok, hint) in CHECKS[argv[0].zfill(2)]():
        print(f"{'PASS' if ok else 'FAIL'}  {label}" + ("" if ok or not hint else f"\n      hint: {hint}"))
        failed += not ok
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
