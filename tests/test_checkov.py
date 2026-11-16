"""Only runs where checkov is installed (make install-checkov): every reference solution must pass the policy scan."""

import shutil
from pathlib import Path

import pytest

from labkit import CHECKOV_SKIPS, Ctx, checkov_tool
from lab_specs import LABS

ROOT = Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.skipif(shutil.which("checkov") is None, reason="checkov not installed")


@pytest.fixture(autouse=True)
def tools_on(monkeypatch):
    # other test modules switch external tools off for the whole run; this file needs checkov
    monkeypatch.delenv("LABKIT_NO_TOOLS", raising=False)


@pytest.mark.parametrize("lab", [k for k in LABS if k not in ("13", "14")])
def test_solution_passes_policy_scan(lab):
    result = checkov_tool(CHECKOV_SKIPS.get(lab))(Ctx(ROOT / "labs" / LABS[lab][0] / "solution"))
    assert result.ok is True, result.detail


def test_policy_scan_catches_an_insecure_storage_account(tmp_path):
    (tmp_path / "main.bicep").write_text(
        "resource sa 'Microsoft.Storage/storageAccounts@2023-05-01' = {\n  name: 'x'\n  location: 'eastus'\n"
        "  sku: { name: 'Standard_LRS' }\n  kind: 'StorageV2'\n  properties: {\n    supportsHttpsTrafficOnly: false\n  }\n}\n"
    )
    assert checkov_tool()(Ctx(tmp_path)).ok is False
