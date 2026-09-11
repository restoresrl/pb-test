from __future__ import annotations

from pathlib import Path

from pb_test_driver import junit

SAMPLE = """\ufeff<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="n_suite_all" tests="3" failures="1" errors="1" time="0.015">
  <testsuite name="n_suite_all" tests="3" failures="1" errors="1" time="0.015">
    <testcase classname="n_test_example" name="test_ok" time="0.000"/>
    <testcase classname="n_test_example" name="test_that_fails" time="0.015">
      <failure message="expected 'a' but was 'b'&#10;second">expected 'a' but was 'b'
second</failure>
    </testcase>
    <testcase classname="n_test_example" name="test_that_raises" time="0.000">
      <error message="Null object reference at line 3 in test_that_raises event of n_test_example."
      >Null object reference at line 3 in test_that_raises event of n_test_example.</error>
    </testcase>
  </testsuite>
</testsuites>
"""


def test_parse_counts_and_statuses() -> None:
    r = junit.parse_text(SAMPLE)
    assert (r.tests, r.failures, r.errors, r.passed) == (3, 1, 1, 1)
    assert not r.ok
    assert [c.status for c in r.cases] == ["pass", "fail", "error"]
    assert r.cases[1].message.splitlines() == ["expected 'a' but was 'b'", "second"]
    assert r.cases[2].message.startswith("Null object reference at line 3")
    assert r.cases[1].time == 0.015


def test_summary_lists_only_non_passing() -> None:
    s = junit.parse_text(SAMPLE).summary()
    lines = s.splitlines()
    assert lines[0] == "n_suite_all: 3 tests, 1 passed, 1 failed, 1 errors"
    assert lines[1].startswith("FAIL n_test_example.test_that_fails: expected 'a'")
    assert lines[-1].startswith("ERROR n_test_example.test_that_raises:")
    assert "test_ok" not in s


def test_parse_file_strips_bom(tmp_path: Path) -> None:
    p = tmp_path / "r.xml"
    p.write_text(SAMPLE, encoding="utf-8")
    assert junit.parse_file(p).tests == 3


def test_rejects_non_junit() -> None:
    import pytest

    with pytest.raises(ValueError):
        junit.parse_text("<html/>")
