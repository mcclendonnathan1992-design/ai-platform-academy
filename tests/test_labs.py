"""The lab checkers must accept the reference solutions and reject blank or broken work."""

import os
from pathlib import Path

import pytest

os.environ["LABKIT_NO_TOOLS"] = "1"  # unit tests never call terraform/docker/az

from lab_check import ROOT, run_lab  # noqa: E402
from lab_specs import LABS  # noqa: E402
from labkit import Ctx, bicep_blocks, passed, tf_blocks  # noqa: E402

SOLVED = [k for k in LABS if k != "14"]  # the capstone has no reference solution


@pytest.mark.parametrize("lab", SOLVED)
def test_reference_solution_passes(lab):
    results = run_lab(lab, "solution")
    failures = [(r.desc, r.detail) for r in results if r.ok is False]
    assert not failures, failures


@pytest.mark.parametrize("lab", list(LABS))
def test_blank_work_fails(lab):
    results = run_lab(lab, "work")
    assert any(r.ok is False for r in results), "a blank work/ folder must not pass"
    assert not passed(results)


def test_broken_drill_files_fail_each_bug_check():
    name, _ = LABS["13"]
    given = ROOT / "labs" / name / "given"
    from lab_specs import LAB13

    ctx = Ctx(given)
    failed = [r.desc for r in (c(ctx) for c in LAB13.checks) if r.ok is False]
    # 3 bugs in each of 4 files
    assert len(failed) == 12, failed


@pytest.mark.parametrize("lab", list(LABS))
def test_each_lab_has_readme_and_work_dir(lab):
    name, _ = LABS[lab]
    base = ROOT / "labs" / name
    readme = (base / "README.md").read_text()
    assert f"make lab-check LAB={lab}" in readme
    assert (base / "work").is_dir()


def test_partial_work_reports_specific_failures(tmp_path):
    (tmp_path / "Dockerfile").write_text("FROM python:latest\nCMD python app.py\n")
    from lab_specs import LAB01

    results = {r.desc: r.ok for r in (c(Ctx(tmp_path)) for c in LAB01.checks)}
    assert results["base image(s) pinned to a tag (not latest)"] is False
    assert results["runs as a numeric non-root user"] is False
    assert results["CMD in exec form"] is False
    assert results["no ADD from a URL"] is True


def test_tf_blocks_parse_nested_braces():
    text = 'resource "a" "b" {\n  x = { y = 1 }\n  dynamic "z" { content {} }\n}\nvariable "v" {\n}\n'
    blocks = tf_blocks(text)
    assert [(b.kind, b.labels) for b in blocks] == [("resource", ("a", "b")), ("variable", ("v",))]


def test_bicep_blocks_handle_loops_and_modules():
    text = (
        "resource v 'Microsoft.Network/virtualNetworks@2024-01-01' = {\n"
        "  properties: { subnets: [for s in subnets: {\n    name: s.name\n  }] }\n}\n"
        "module m 'modules/x.bicep' = {\n  name: 'x'\n}\n"
        "resource sub 'Microsoft.Network/x@2024-01-01' = [for i in range(0, 2): {\n  name: 'n${i}'\n}]\n"
    )
    kinds = [(b.kind, b.labels[1]) for b in bicep_blocks(text)]
    assert ("resource", "Microsoft.Network/virtualNetworks@2024-01-01") in kinds
    assert ("module", "modules/x.bicep") in kinds
    assert ("resource", "Microsoft.Network/x@2024-01-01") in kinds


def test_arm_securestring_plaintext_is_rejected(tmp_path):
    lab = tmp_path / "labs"
    (lab / "given").mkdir(parents=True)
    (lab / "work").mkdir()
    (lab / "given" / "template.json").write_text(
        '{"parameters":{"pw":{"type":"securestring"},"n":{"type":"string"}}}'
    )
    (lab / "work" / "parameters.json").write_text(
        '{"$schema":"x/deploymentParameters.json#","contentVersion":"1.0.0.0","parameters":{"pw":{"value":"hunter2"},"n":{"value":"a"}}}'
    )
    from lab_specs import _secure_uses_kv

    assert "plaintext" in _secure_uses_kv(Ctx(lab / "work"))
