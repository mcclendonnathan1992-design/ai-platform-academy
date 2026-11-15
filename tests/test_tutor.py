import json

import pytest

from tutor import core


@pytest.fixture
def fake_modules(tmp_path, monkeypatch):
    for name in ("00-setup", "04-kubernetes", "05-terraform"):
        d = tmp_path / name
        d.mkdir()
        (d / "README.md").write_text(f"# {name}\nPods run containers.")
    monkeypatch.setattr(core, "MODULES_DIR", tmp_path)
    return tmp_path


def test_resolve_by_number_and_name(fake_modules):
    assert core.resolve_module("4") == "04-kubernetes"
    assert core.resolve_module("04") == "04-kubernetes"
    assert core.resolve_module("terraform") == "05-terraform"


def test_resolve_unknown_and_ambiguous(fake_modules):
    with pytest.raises(core.TutorError):
        core.resolve_module("nope")
    with pytest.raises(core.TutorError):
        core.resolve_module("e")  # substring matches several


def test_ask_sends_lesson_and_question(fake_modules):
    seen = {}

    def fake(messages):
        seen["messages"] = messages
        return "a pod is the smallest unit"

    assert core.ask("04", "what is a pod?", chat_fn=fake) == "a pod is the smallest unit"
    assert "Pods run containers" in seen["messages"][1]["content"]
    assert "what is a pod?" in seen["messages"][1]["content"]


def test_parse_questions():
    text = "Here you go:\n1. What is a pod?\n2) Why probes?\n- How do HPAs scale?\nnot a question"
    assert core.parse_questions(text) == ["What is a pod?", "Why probes?", "How do HPAs scale?"]


def test_make_questions_errors_when_unusable(fake_modules):
    with pytest.raises(core.TutorError):
        core.make_questions("04", chat_fn=lambda m: "no questions here")


@pytest.mark.parametrize("reply,score", [("Correct. Nice.", 1.0), ("Partly right", 0.5), ("Incorrect, because", 0.0), ("hm", 0.0)])
def test_grade(fake_modules, reply, score):
    assert core.grade("04", "q?", "a", chat_fn=lambda m: reply)[0] == score


def test_progress_roundtrip(fake_modules, tmp_path):
    p = tmp_path / "progress.json"
    assert core.load_progress(p) == {}
    core.mark_done("04", path=p)
    assert json.loads(p.read_text()) == {"04-kubernetes": "done"}
    p.write_text("not json")
    assert core.load_progress(p) == {}


def test_missing_readme(fake_modules):
    (fake_modules / "04-kubernetes" / "README.md").unlink()
    with pytest.raises(core.TutorError):
        core.module_text("04")
