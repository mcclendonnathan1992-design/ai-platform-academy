import pytest

from new_service import scaffold


def test_scaffold_replaces_name(tmp_path):
    target = scaffold("demo-svc", tmp_path)
    text = (target / "k8s" / "deployment.yaml").read_text()
    assert "__NAME__" not in text and "demo-svc" in text
    assert (target / "app" / "Dockerfile").exists()


@pytest.mark.parametrize("bad", ["Bad", "-x", "x_y", "", "a" * 64])
def test_rejects_bad_names(tmp_path, bad):
    with pytest.raises(ValueError):
        scaffold(bad, tmp_path)


def test_refuses_existing(tmp_path):
    scaffold("svc", tmp_path)
    with pytest.raises(FileExistsError):
        scaffold("svc", tmp_path)
