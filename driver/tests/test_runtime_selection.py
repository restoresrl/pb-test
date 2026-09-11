from __future__ import annotations

from pathlib import Path

import pytest

from pb_test_driver import run


def sidecar(exe: Path, runtime: Path) -> None:
    exe.with_suffix(".xml").write_text(
        f"<Application><RuntimePath>{runtime}</RuntimePath></Application>", encoding="utf-8"
    )


def test_sidecar_wins_over_newest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = tmp_path / "Runtime 19.2"
    runtime.mkdir()
    exe = tmp_path / "sample.exe"
    sidecar(exe, runtime)
    monkeypatch.setattr(run, "find_runtime_dir", lambda version=None: tmp_path / "newest")
    assert run.select_runtime(exe, None, None) == runtime


def test_mismatch_rejected_before_start(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    exe = tmp_path / "sample.exe"
    exe.touch()
    sidecar(exe, tmp_path / "Runtime 22.2")
    requested = tmp_path / "Runtime 19.2"
    requested.mkdir()
    monkeypatch.setattr(run, "find_runtime_dir", lambda version=None: requested)
    with pytest.raises(ValueError, match="RuntimePath"):
        run.start(exe, runtime_version="19.2")
    assert not (tmp_path / "pb.ini").exists()


def test_matching_explicit_runtime(tmp_path: Path) -> None:
    exe = tmp_path / "sample.exe"
    sidecar(exe, tmp_path)
    assert run.select_runtime(exe, None, tmp_path) == tmp_path


def test_missing_sidecar_uses_explicit_directory(tmp_path: Path) -> None:
    assert run.select_runtime(tmp_path / "sample.exe", None, tmp_path) == tmp_path


def test_missing_runtime_fails(tmp_path: Path) -> None:
    exe = tmp_path / "sample.exe"
    sidecar(exe, tmp_path / "absent")
    with pytest.raises(FileNotFoundError, match="runtime directory"):
        run.select_runtime(exe, None, None)


def test_malformed_sidecar_fails(tmp_path: Path) -> None:
    exe = tmp_path / "sample.exe"
    exe.with_suffix(".xml").write_text("<Application>", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid runtime XML"):
        run.select_runtime(exe, None, None)


def test_runtime_options_are_exclusive(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not both"):
        run.select_runtime(tmp_path / "sample.exe", "19.2", tmp_path)


def test_relative_sidecar_path(tmp_path: Path) -> None:
    exe = tmp_path / "sample.exe"
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    sidecar(exe, Path("runtime"))
    assert run.select_runtime(exe, None, None) == runtime
