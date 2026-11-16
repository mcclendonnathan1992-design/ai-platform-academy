import az_tool


def test_sweep_only_touches_lab_prefix(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(az_tool, "az", lambda *a: ["rg-lab-dev", "rg-lab-aks", "rg-production", "NetworkWatcherRG"] if a[0] == "group" else {"name": "personal"})
    monkeypatch.setattr(az_tool.subprocess, "run", lambda cmd, **k: calls.append(cmd))
    monkeypatch.setattr("builtins.input", lambda _: "yes")
    assert az_tool.sweep(delete=True) == 0
    deleted = [c[c.index("--name") + 1] for c in calls]
    assert sorted(deleted) == ["rg-lab-aks", "rg-lab-dev"]
    assert "rg-production" in capsys.readouterr().out  # listed as not touched


def test_dry_run_deletes_nothing(monkeypatch):
    calls = []
    monkeypatch.setattr(az_tool, "az", lambda *a: ["rg-lab-dev"])
    monkeypatch.setattr(az_tool.subprocess, "run", lambda cmd, **k: calls.append(cmd))
    assert az_tool.sweep(delete=False) == 0
    assert calls == []


def test_must_type_yes(monkeypatch):
    calls = []
    monkeypatch.setattr(az_tool, "az", lambda *a: ["rg-lab-dev"] if a[0] == "group" else {"name": "x"})
    monkeypatch.setattr(az_tool.subprocess, "run", lambda cmd, **k: calls.append(cmd))
    monkeypatch.setattr("builtins.input", lambda _: "y")
    assert az_tool.sweep(delete=True) == 1
    assert calls == []
