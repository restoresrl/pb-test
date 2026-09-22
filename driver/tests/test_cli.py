from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from click.testing import CliRunner

from pb_test_driver import run
from pb_test_driver.cli import cli


@pytest.mark.parametrize(
    ("statuses", "exit_code", "expected"),
    [(("pass",), 0, 0), (("fail",), 1, 1), (("pass",), 9, 3), ((), 0, 3)],
)
def test_run_exit_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    write_report: Callable[..., dict[str, Any]],
    statuses: tuple[str, ...],
    exit_code: int,
    expected: int,
) -> None:
    exe = tmp_path / "different-from-app.exe"
    exe.touch()
    out = tmp_path / "result.json"
    stopped: list[str] = []

    def start(*args: object, **kwargs: object) -> SimpleNamespace:
        assert args[1] == ""  # No command-line test protocol.
        path = tmp_path / "sample_test.json"
        request = json.loads(path.read_text())
        path.rename(str(path) + ".active")
        write_report(out, request["request_id"], statuses=statuses)
        return SimpleNamespace(id="sample")

    monkeypatch.setattr(run, "start", start)
    monkeypatch.setattr(
        run,
        "wait",
        lambda *args: {"timed_out": False, "runtime_error": None, "exit_code": exit_code},
    )
    monkeypatch.setattr(run, "stop", lambda run_id: stopped.append(run_id))
    result = CliRunner().invoke(
        cli, ["run", str(exe), "--application", "sample", "--out", str(out)]
    )
    assert result.exit_code == expected, result.output
    assert stopped == ["sample"]
    assert not (tmp_path / "sample_test.json.lock").exists()


def test_ide_prepare_and_timeout_do_not_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("IDE flow must not launch or stop processes")

    monkeypatch.setattr(run, "start", forbidden)
    monkeypatch.setattr(run, "stop", forbidden)
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "prepare",
            "--application",
            "sample",
            "--work-dir",
            str(tmp_path),
            "--out",
            str(tmp_path / "result.json"),
        ],
    )
    assert result.exit_code == 0, result.output
    ticket = json.loads(result.output)
    result = runner.invoke(cli, ["wait", ticket["receipt"], "--timeout", "0"])
    assert result.exit_code == 4
    assert Path(ticket["request_path"]).exists()
    result = runner.invoke(cli, ["cleanup", ticket["receipt"]])
    assert result.exit_code == 0


def test_launch_failure_cancels_own_pending_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    exe = tmp_path / "sample.exe"
    exe.touch()

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("launch failed")

    monkeypatch.setattr(run, "start", fail)
    result = CliRunner().invoke(
        cli, ["run", str(exe), "--application", "sample", "--out", str(tmp_path / "r.json")]
    )
    assert result.exit_code == 3
    assert not (tmp_path / "sample_test.json").exists()
    assert not (tmp_path / "sample_test.json.lock").exists()
