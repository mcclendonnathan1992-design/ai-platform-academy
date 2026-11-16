"""Safety rails for practising on a real Azure subscription.

    python scripts/az_tool.py preflight    # who am I, which subscription, is it OK to deploy here?
    python scripts/az_tool.py sweep        # list leftover practice resource groups (dry run)
    python scripts/az_tool.py sweep --delete   # delete them (asks you to type yes)

Convention: every practice resource group is named  rg-lab-<something>.  The sweep only ever touches
groups with that prefix, so it cannot delete anything else.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys

PREFIX = "rg-lab-"


def az(*args: str) -> object:
    if shutil.which("az") is None:
        sys.exit("The Azure CLI (az) is not installed here. In your Codespace: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash")
    p = subprocess.run(["az", *args, "-o", "json"], capture_output=True, text=True)
    if p.returncode:
        msg = p.stderr.strip().splitlines()[-1] if p.stderr.strip() else "az failed"
        sys.exit(f"{msg}\nSign in first:  az login --use-device-code")
    return json.loads(p.stdout or "null")


def preflight() -> int:
    acct = az("account", "show")
    print(f"Signed in as : {acct['user']['name']}")
    print(f"Subscription : {acct['name']}   ({acct['id']})")
    print(f"Tenant       : {acct['tenantId']}")
    print("\nBefore you deploy anything, check ALL of these:")
    print("  [ ] This is your PERSONAL practice subscription, not an employer or customer tenant.")
    print("  [ ] A budget alert exists (Cost Management -> Budgets), e.g. $10/month, alert at 50% and 90%.")
    print(f"  [ ] Resource groups are named {PREFIX}<something> so the sweep can find them.")
    print("  [ ] You will destroy it today:  terraform destroy   or   make az-sweep-delete")
    groups = az("group", "list", "--query", "[].name")
    mine = [g for g in groups if g.startswith(PREFIX)]
    print(f"\nPractice resource groups currently in this subscription: {len(mine)}")
    for g in mine:
        print(f"  - {g}")
    return 0


def sweep(delete: bool) -> int:
    groups = az("group", "list", "--query", "[].name")
    mine = sorted(g for g in groups if g.startswith(PREFIX))
    others = sorted(g for g in groups if not g.startswith(PREFIX))
    if not mine:
        print(f"Nothing to clean: no resource groups start with {PREFIX}.")
    else:
        print(f"Practice resource groups ({PREFIX}*):")
        for g in mine:
            print(f"  - {g}")
    if others:
        print(f"\nNot touched ({len(others)} groups without the {PREFIX} prefix):")
        for g in others:
            print(f"  - {g}")
    if not mine or not delete:
        if mine:
            print("\nDry run. To delete the practice groups:  make az-sweep-delete")
        return 0
    sub = az("account", "show")["name"]
    print(f"\nThis will DELETE {len(mine)} resource group(s) in subscription '{sub}'.")
    if input("Type yes to continue: ").strip().lower() != "yes":
        print("Cancelled.")
        return 1
    for g in mine:
        subprocess.run(["az", "group", "delete", "--name", g, "--yes", "--no-wait"], check=False)
        print(f"  deleting {g} (runs in the background)")
    print("\nDeletes continue in Azure. Check in a few minutes:  make az-sweep")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="az_tool")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("preflight")
    s = sub.add_parser("sweep")
    s.add_argument("--delete", action="store_true")
    args = ap.parse_args(argv)
    return preflight() if args.cmd == "preflight" else sweep(args.delete)


if __name__ == "__main__":
    raise SystemExit(main())
