from eval_gateway import load_cases, passes
from benchmark import percentile


def test_golden_file_is_valid():
    cases = load_cases()
    assert cases and all("prompt" in c and c["must_contain"] for c in cases)


def test_passes_is_case_insensitive_and_requires_all():
    assert passes("It is PARIS.", ["paris"])
    assert not passes("Lyon", ["paris"])
    assert not passes("paris", ["paris", "france"])


def test_percentile():
    assert percentile([1, 2, 3, 4, 5], 50) == 3
    assert percentile([5], 95) == 5
