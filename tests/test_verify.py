import verify


def test_every_module_has_a_check():
    assert sorted(verify.CHECKS) == [f"{i:02d}" for i in range(10)]


def test_usage_error():
    assert verify.main([]) == 2
    assert verify.main(["99"]) == 2


def test_files_exist_reports_missing():
    ok, msg = verify.files_exist("README.md.nope")
    assert not ok and "nope" in msg
