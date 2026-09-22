from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from pb_test_driver import protocol, requests


def test_roundtrip(tmp_path: Path, write_report: Callable[..., dict[str, Any]]) -> None:
    path = tmp_path / "result.json"
    write_report(path, statuses=("pass", "fail", "error"))
    data = protocol.report(path, "abc123", "sample")
    assert not data["ok"]
    assert data["tests"] == 3
    assert "Ω" in data["cases"][1]["message"]


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("schema_version", 2),
        ("schema_version", True),
        ("completed", False),
        ("completed", 1),
        ("tests", 9),
        ("passed", True),
        ("cases", None),
        ("runner_errors", [42]),
        ("application", ""),
    ],
)
def test_rejects_invalid_reports(
    tmp_path: Path, write_report: Callable[..., dict[str, Any]], key: str, value: Any
) -> None:
    path = tmp_path / "result.json"
    data = write_report(path)
    data[key] = value
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        protocol.report(path)


@pytest.mark.parametrize("elapsed", [-1, float("inf"), float("nan"), True])
def test_bad_times(
    tmp_path: Path, write_report: Callable[..., dict[str, Any]], elapsed: float
) -> None:
    path = tmp_path / "result.json"
    data = write_report(path)
    data["cases"][0]["time"] = elapsed
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        protocol.report(path)


def test_duplicate_key(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        protocol.report(path)


def test_zero_tests_and_runner_error_are_not_green(
    tmp_path: Path, write_report: Callable[..., dict[str, Any]]
) -> None:
    path = tmp_path / "result.json"
    write_report(path, statuses=())
    assert not protocol.report(path)["ok"]
    data = write_report(path)
    data["runner_errors"] = ["host cleanup failed"]
    path.write_text(json.dumps(data), encoding="utf-8")
    assert not protocol.report(path)["ok"]


def test_request_lifecycle(tmp_path: Path, write_report: Callable[..., dict[str, Any]]) -> None:
    out = tmp_path / "résultats Ω" / "result.json"
    ticket = requests.prepare("sample", tmp_path, out)
    receipt = ticket["receipt"]
    assert requests.status(receipt)["state"] == "pending"
    path = Path(ticket["request_path"])
    assert json.loads(path.read_text(encoding="utf-8"))["output"] == str(out)
    with pytest.raises(FileExistsError):
        requests.prepare("sample", tmp_path, tmp_path / "another.json")
    path.rename(str(path) + ".active")  # What the PB request reader does.
    assert requests.wait(receipt, 0)["timed_out"]
    with pytest.raises(ValueError, match="active"):
        requests.cleanup(receipt)
    write_report(out, ticket["request"]["request_id"])
    assert requests.wait(receipt, 0)["results"]["ok"]
    requests.cleanup(receipt)
    assert out.is_file() and Path(receipt).is_file()
    assert not Path(str(path) + ".active").exists()
    assert requests.status(receipt)["state"] == "completed"
    next_ticket = requests.prepare("sample", tmp_path, tmp_path / "next.json")
    with pytest.raises(ValueError, match="reservation"):
        requests.cleanup(receipt)
    assert Path(next_ticket["request_path"]).exists()


def test_completed_cleanup_archives_second_launch_diagnostic(
    tmp_path: Path, write_report: Callable[..., dict[str, Any]]
) -> None:
    out = tmp_path / "result.json"
    ticket = requests.prepare("sample", tmp_path, out)
    path = Path(ticket["request_path"])
    path.rename(str(path) + ".active")
    diagnostic = Path(str(path) + ".active.error.json")
    diagnostic.write_text('{"error":"already active"}', encoding="utf-8")
    write_report(out, ticket["request"]["request_id"])
    requests.cleanup(ticket["receipt"])
    assert not diagnostic.exists()
    assert Path(ticket["receipt"] + ".error.json").exists()
    requests.prepare("sample", tmp_path, tmp_path / "next.json")


def test_status_handles_acquisition_between_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ticket = requests.prepare("sample", tmp_path, tmp_path / "result.json")
    pending = Path(ticket["request_path"])
    active = Path(str(pending) + ".active")
    original = protocol.load_object
    first = True

    def load(path: str | Path) -> dict[str, Any]:
        nonlocal first
        if Path(path) == active and first:
            first = False
            pending.rename(active)
            raise FileNotFoundError("acquired after active lookup")
        return original(path)

    monkeypatch.setattr(protocol, "load_object", load)
    assert requests.status(ticket["receipt"])["state"] == "active"


def test_pending_cancel_and_expiry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ticket = requests.prepare("sample", tmp_path, tmp_path / "result.json")
    monkeypatch.setattr(requests.time, "time", lambda: ticket["request"]["expires_at"])
    assert requests.wait(ticket["receipt"], 0)["state"] == "expired"
    requests.cleanup(ticket["receipt"])
    assert not Path(ticket["request_path"]).exists()


def test_no_partial_publish(tmp_path: Path) -> None:
    path = tmp_path / "existing.json"
    path.write_text("original", encoding="utf-8")
    with pytest.raises(FileExistsError):
        requests._publish(path, {"replacement": True})
    assert path.read_text() == "original"
    assert not list(tmp_path.glob("*.tmp"))


def test_invalid_output_and_identity(
    tmp_path: Path, write_report: Callable[..., dict[str, Any]]
) -> None:
    out = tmp_path / "result.json"
    ticket = requests.prepare("sample", tmp_path, out)
    write_report(out, "old-request")
    assert requests.status(ticket["receipt"])["state"] == "invalid"
    with pytest.raises(ValueError):
        requests.cleanup(ticket["receipt"])
    assert Path(ticket["request_path"]).exists()


def test_rejected_request_is_data(tmp_path: Path) -> None:
    ticket = requests.prepare("sample", tmp_path, tmp_path / "result.json")
    path = Path(ticket["request_path"])
    active = Path(str(path) + ".active")
    path.rename(active)
    Path(str(active) + ".error.json").write_text('{"error":"bad request"}', encoding="utf-8")
    assert requests.status(ticket["receipt"])["error"] == "bad request"
    assert requests.wait(ticket["receipt"], 0)["state"] == "rejected"
    with pytest.raises(ValueError):
        requests.cleanup(ticket["receipt"])


@pytest.mark.parametrize("name", ["", "../bad", "app.exe", "a/b", "1app"])
def test_bad_application_name(tmp_path: Path, name: str) -> None:
    with pytest.raises(ValueError):
        requests.prepare(name, tmp_path, tmp_path / "result.json")


def test_other_target_and_other_directory(tmp_path: Path) -> None:
    requests.prepare("a", tmp_path, tmp_path / "a.json")
    requests.prepare("b", tmp_path, tmp_path / "b.json")
    other = tmp_path / "other"
    other.mkdir()
    requests.prepare("a", other, other / "a.json")


@pytest.mark.parametrize("timeout", [-1.0, float("inf"), float("nan")])
def test_invalid_wait_timeout(tmp_path: Path, timeout: float) -> None:
    ticket = requests.prepare("sample", tmp_path, tmp_path / "result.json")
    with pytest.raises(ValueError, match="finite"):
        requests.wait(ticket["receipt"], timeout)


def test_documented_schemas(tmp_path: Path, write_report: Callable[..., dict[str, Any]]) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schemas = Path(__file__).resolve().parents[2] / "schemas"
    if not schemas.is_dir():
        pytest.skip("protocol schemas ship in the repository archive, not the driver sdist")
    ticket = requests.prepare("sample", tmp_path, tmp_path / "result.json")
    data = write_report(tmp_path / "result.json", ticket["request"]["request_id"])
    for name, document in (("request", ticket["request"]), ("result", data)):
        schema = json.loads((schemas / f"{name}.schema.json").read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.validate(document, schema)


@pytest.mark.parametrize(
    "relative",
    [
        "sample_test.json",
        "sample_test.json.active",
        "sample_test.json.active.error.json",
        "sample_test.json.lock/owner.json",
        "sample_test.json.active/nested.json",
    ],
)
def test_output_cannot_alias_control_files(tmp_path: Path, relative: str) -> None:
    with pytest.raises(ValueError, match="control paths"):
        requests.prepare("sample", tmp_path, tmp_path / relative)
    assert not list(tmp_path.iterdir())


def test_existing_output_is_preserved(tmp_path: Path) -> None:
    out = tmp_path / "result.json"
    out.write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError):
        requests.prepare("sample", tmp_path, out)
    assert out.read_text() == "keep"
    assert not list(tmp_path.glob("*.lock"))
