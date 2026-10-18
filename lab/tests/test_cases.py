"""Every case fails its check as shipped, and passes once fixed. The fixes live in solutions/."""

import importlib
from pathlib import Path

import pytest

from dove.__main__ import CASES
from dove.checks import CHECKS


@pytest.mark.parametrize("number", list(CASES))
def test_case_is_broken_as_shipped(number):
    case = importlib.import_module(f"cases.{CASES[number][0]}")

    results = CHECKS[number](case)

    assert not all(ok for _, ok in results)


@pytest.mark.parametrize("number", list(CASES))
def test_case_passes_with_a_real_fix(number):
    fixed = importlib.import_module(f"tests.solutions.{CASES[number][0]}")

    failed = [label for label, ok in CHECKS[number](fixed) if not ok]

    assert failed == []


@pytest.mark.parametrize("number", list(CASES))
def test_a_fix_changes_only_a_few_lines(number):
    name = CASES[number][0]
    shipped = Path(f"cases/{name}.py").read_text().splitlines()
    fixed = Path(f"tests/solutions/{name}.py").read_text().splitlines()

    changed = len(set(fixed) - set(shipped)) + len(set(shipped) - set(fixed))

    assert 0 < changed <= 16
