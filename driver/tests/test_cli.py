from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

from pb_test_driver import run
from pb_test_driver.cli import cli


@pytest.mark.parametrize(
    ("body", "exit_code", "expected"),
    [
        ('<testcase name="pass"/>', 0, 0),
        ('<testcase name="fail"><failure>wrong</failure></testcase>', 1, 1),
        ('<testcase name="pass"/>', 9, 3),
        ("", 0, 3),
    ],
)
def test_run_exit_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    body: str,
    exit_code: int,
    expected: int,
) -> None:
    exe = tmp_path / "sample.exe"
    exe.touch()
    out = tmp_path / "result.xml"
    stopped: list[str] = []

    def start(*args: object, **kwargs: object) -> SimpleNamespace:
        out.write_text(f'<testsuite name="sample">{body}</testsuite>', encoding="utf-8")
        return SimpleNamespace(id="sample")

    monkeypatch.setattr(run, "start", start)
    monkeypatch.setattr(
        run,
        "wait",
        lambda *args: {"timed_out": False, "runtime_error": None, "exit_code": exit_code},
    )
    monkeypatch.setattr(run, "stop", lambda run_id: stopped.append(run_id))
    result = CliRunner().invoke(cli, ["run", str(exe), "--out", str(out)])
    assert result.exit_code == expected, result.output
    assert stopped == ["sample"]
