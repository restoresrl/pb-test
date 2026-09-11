"""Start, watch and stop a PowerBuilder executable.

What this module knows that a plain `subprocess` does not:

- runtime DLLs can be selected by RuntimePath in the adjacent executable
  XML, independently of PATH; conflicting explicit requests are rejected;
- otherwise the runtime directory is prepended to the child's PATH;
- UI Automation is off unless `pb.ini` next to the exe says
  `[Application] ACCESSIBILITY=1`;
- a runtime error is a modal `#32770` dialog titled "PowerBuilder
  application execution error (R00nn)". The process stays alive until OK is
  pressed, and UI Automation does not list the dialog; the win32 backend does.
"""

from __future__ import annotations

import configparser
import os
import re
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

RUNTIME_ROOT = Path(r"C:\Program Files (x86)\Appeon\Common\PowerBuilder")
ERROR_TITLE = re.compile(r"^PowerBuilder application execution error \((R\d+)\)", re.IGNORECASE)


@dataclass
class Run:
    id: str
    exe: Path
    args: str
    cwd: Path
    runtime_dir: Path | None
    process: subprocess.Popen[bytes]
    started: float = field(default_factory=time.monotonic)
    runtime_error: dict[str, str] | None = None

    @property
    def pid(self) -> int:
        return self.process.pid

    def info(self) -> dict[str, Any]:
        return {
            "run_id": self.id,
            "pid": self.pid,
            "exe": str(self.exe),
            "args": self.args,
            "cwd": str(self.cwd),
            "runtime_dir": str(self.runtime_dir) if self.runtime_dir else None,
            "running": self.process.poll() is None,
            "exit_code": self.process.poll(),
            "runtime_error": self.runtime_error,
        }


_RUNS: dict[str, Run] = {}


def list_runtime_dirs() -> list[Path]:
    """Every `Runtime <version>` directory, newest version first."""
    if not RUNTIME_ROOT.is_dir():
        return []

    def key(p: Path) -> tuple[int, ...]:
        m = re.search(r"Runtime (\d+(?:\.\d+)*)", p.name)
        return tuple(int(x) for x in m.group(1).split(".")) if m else ()

    dirs = [p for p in RUNTIME_ROOT.iterdir() if p.is_dir() and p.name.startswith("Runtime ")]
    return sorted(dirs, key=key, reverse=True)


def find_runtime_dir(version: str | None = None) -> Path | None:
    """Pick the runtime directory: an exact or prefix match on `version`, else the newest.

    This searches installed directories, not loaded modules. `select_runtime`
    also checks the executable's XML RuntimePath before choosing the child's PATH.
    """
    dirs = list_runtime_dirs()
    if version:
        for d in dirs:
            if d.name == f"Runtime {version}" or d.name.startswith(f"Runtime {version}."):
                return d
        return None
    return dirs[0] if dirs else None


def runtime_from_sidecar(exe: Path) -> Path | None:
    """Read the executable's RuntimePath without changing its deployment file."""
    sidecar = exe.with_suffix(".xml")
    if not sidecar.is_file():
        return None
    try:
        value = ET.parse(sidecar).getroot().findtext("RuntimePath")
    except ET.ParseError as exc:
        raise ValueError(f"invalid runtime XML {sidecar}: {exc}") from exc
    if not value or not value.strip():
        return None
    path = Path(value.strip())
    return (path if path.is_absolute() else exe.parent / path).resolve()


def select_runtime(exe: Path, version: str | None, directory: str | Path | None) -> Path | None:
    """Reject a sidecar/PATH mismatch rather than silently testing another runtime."""
    if version and directory:
        raise ValueError("pass runtime_version or runtime_dir, not both")
    sidecar = runtime_from_sidecar(exe)
    requested = (
        Path(directory).resolve() if directory else find_runtime_dir(version) if version else None
    )
    if version and requested is None:
        raise FileNotFoundError(
            f"no PowerBuilder runtime {version} under {RUNTIME_ROOT}; "
            f"available: {[d.name for d in list_runtime_dirs()]}"
        )
    if sidecar is not None and requested is not None and sidecar != requested.resolve():
        raise ValueError(
            f"{exe.with_suffix('.xml')} selects {sidecar}, but the requested runtime is "
            f"{requested}; correct the test deployment's RuntimePath before running"
        )
    selected = sidecar or requested or find_runtime_dir()
    if selected is not None and not selected.is_dir():
        raise FileNotFoundError(f"runtime directory not found: {selected}")
    return selected


def ensure_accessibility(exe_dir: Path) -> str:
    """Make sure `pb.ini` next to the exe enables UI Automation.

    Returns `created`, `updated` or `present`. An existing file is rewritten only
    when the key is missing or not 1, and configparser keeps the other sections.
    """
    ini = exe_dir / "pb.ini"
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str  # type: ignore[assignment,method-assign]
    if ini.exists():
        parser.read(ini, encoding="utf-8")
        if parser.has_option("Application", "ACCESSIBILITY"):
            if parser.get("Application", "ACCESSIBILITY").strip() == "1":
                return "present"
        status = "updated"
    else:
        status = "created"
    if not parser.has_section("Application"):
        parser.add_section("Application")
    parser.set("Application", "ACCESSIBILITY", "1")
    with ini.open("w", encoding="utf-8", newline="\r\n") as fh:
        parser.write(fh, space_around_delimiters=False)
    return status


def child_env(runtime_dir: Path | None) -> dict[str, str]:
    env = dict(os.environ)
    if runtime_dir is not None:
        env["PATH"] = str(runtime_dir) + os.pathsep + env.get("PATH", "")
    return env


def start(
    exe: str | Path,
    args: str = "",
    work_dir: str | Path | None = None,
    runtime_version: str | None = None,
    runtime_dir: str | Path | None = None,
    accessibility: bool = True,
) -> Run:
    exe_path = Path(exe).resolve()
    if not exe_path.is_file():
        raise FileNotFoundError(f"executable not found: {exe_path}")
    cwd = Path(work_dir).resolve() if work_dir else exe_path.parent
    rt = select_runtime(exe_path, runtime_version, runtime_dir)
    if accessibility:
        ensure_accessibility(exe_path.parent)
    command = f'"{exe_path}" {args}'.strip()
    process = subprocess.Popen(command, cwd=str(cwd), env=child_env(rt))
    run = Run(
        id=uuid.uuid4().hex[:8], exe=exe_path, args=args, cwd=cwd, runtime_dir=rt, process=process
    )
    _RUNS[run.id] = run
    return run


def get(run_id: str) -> Run:
    try:
        return _RUNS[run_id]
    except KeyError:
        raise KeyError(f"unknown run_id {run_id!r}; known: {sorted(_RUNS)}") from None


def runs() -> list[dict[str, Any]]:
    return [r.info() for r in _RUNS.values()]


def find_error_dialog(pid: int) -> dict[str, str] | None:
    """The PowerBuilder runtime error dialog of `pid`, if one is showing.

    Uses the win32 backend on purpose: the UIA top-level enumeration of the process
    did not list this dialog on PB 2022 R3.
    """
    from pywinauto import findwindows

    for el in findwindows.find_elements(process=pid, backend="win32", top_level_only=True):
        title = el.name or ""
        if el.class_name == "#32770" and ERROR_TITLE.match(title):
            from pywinauto.controls.hwndwrapper import HwndWrapper

            dialog = HwndWrapper(el)
            texts = [c.window_text() for c in dialog.children() if c.class_name() == "Static"]
            text = "\n".join(t for t in texts if t.strip())
            code = ERROR_TITLE.match(title)
            return {"title": title, "text": text, "code": code.group(1) if code else ""}
    return None


def dismiss_error_dialog(pid: int) -> bool:
    from pywinauto import findwindows
    from pywinauto.controls.hwndwrapper import HwndWrapper

    for el in findwindows.find_elements(process=pid, backend="win32", top_level_only=True):
        if el.class_name == "#32770" and ERROR_TITLE.match(el.name or ""):
            dialog = HwndWrapper(el)
            for c in dialog.children():
                if c.class_name() == "Button":
                    c.click()
                    return True
    return False


def wait(
    run_id: str, timeout: float = 60.0, dismiss_error: bool = True, poll: float = 0.5
) -> dict[str, Any]:
    """Wait until the process exits, a runtime error dialog appears, or the timeout.

    A runtime error is reported as data, not raised: `runtime_error` carries the
    dialog title, its text (event, object and line), and the R-code. With
    `dismiss_error` the OK button is pressed so the process can terminate.
    """
    run = get(run_id)
    deadline = time.monotonic() + timeout
    while True:
        code = run.process.poll()
        if code is not None:
            return {
                **run.info(),
                "exited": True,
                "timed_out": False,
                "seconds": round(time.monotonic() - run.started, 3),
            }
        err = find_error_dialog(run.pid)
        if err is not None:
            run.runtime_error = err
            if dismiss_error:
                dismiss_error_dialog(run.pid)
                try:
                    run.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    pass
            return {
                **run.info(),
                "exited": run.process.poll() is not None,
                "timed_out": False,
                "seconds": round(time.monotonic() - run.started, 3),
            }
        if time.monotonic() >= deadline:
            return {
                **run.info(),
                "exited": False,
                "timed_out": True,
                "seconds": round(time.monotonic() - run.started, 3),
            }
        time.sleep(poll)


def stop(run_id: str) -> dict[str, Any]:
    run = get(run_id)
    if run.process.poll() is None:
        run.process.kill()
        try:
            run.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
    return run.info()
