from __future__ import annotations

from pathlib import Path

from pb_test_driver import run


def test_ensure_accessibility_creates_ini(tmp_path: Path) -> None:
    assert run.ensure_accessibility(tmp_path) == "created"
    text = (tmp_path / "pb.ini").read_text(encoding="utf-8")
    assert "[Application]" in text and "ACCESSIBILITY=1" in text
    assert run.ensure_accessibility(tmp_path) == "present"


def test_ensure_accessibility_keeps_other_sections(tmp_path: Path) -> None:
    (tmp_path / "pb.ini").write_text(
        "[Database]\nDBMS=ODBC\n\n[Application]\nACCESSIBILITY=0\n", encoding="utf-8"
    )
    assert run.ensure_accessibility(tmp_path) == "updated"
    text = (tmp_path / "pb.ini").read_text(encoding="utf-8")
    assert "DBMS=ODBC" in text
    assert "ACCESSIBILITY=1" in text
    assert "ACCESSIBILITY=0" not in text


def test_error_title_regex() -> None:
    m = run.ERROR_TITLE.match("PowerBuilder application execution error (R0002)")
    assert m and m.group(1) == "R0002"
    assert run.ERROR_TITLE.match("UIA Probe") is None


def test_child_env_prepends_runtime(tmp_path: Path) -> None:
    env = run.child_env(tmp_path)
    assert env["PATH"].startswith(str(tmp_path))
    assert run.child_env(None)["PATH"] == run.os.environ.get("PATH", "")


def test_find_runtime_dir_prefix(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    for name in ("Runtime 19.2.0.2803", "Runtime 22.2.0.3397", "Runtime 25.1.0.6430", "Other"):
        (tmp_path / name).mkdir()
    monkeypatch.setattr(run, "RUNTIME_ROOT", tmp_path)
    newest = run.find_runtime_dir()
    assert newest is not None and newest.name == "Runtime 25.1.0.6430"
    exact = run.find_runtime_dir("22.2")
    assert exact is not None and exact.name == "Runtime 22.2.0.3397"
    prefix = run.find_runtime_dir("22")
    assert prefix is not None and prefix.name == "Runtime 22.2.0.3397"
    assert run.find_runtime_dir("21") is None
