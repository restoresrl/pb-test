"""CLI for JSON test requests, executable runs and UI inspection."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

from pb_test_driver import __version__, protocol, requests, run, ui


def show(data: dict[str, Any]) -> None:
    click.echo(json.dumps(data, indent=2, ensure_ascii=False))


@click.group()
@click.version_option(__version__, prog_name="pb-test")
def cli() -> None:
    """Run and observe PowerBuilder applications."""


@cli.command("prepare")
@click.option("--application", required=True, help="Application object name, not the EXE name")
@click.option("--work-dir", required=True, type=click.Path(exists=True, file_okay=False))
@click.option("--out", required=True, type=click.Path(dir_okay=False))
@click.option("--suite", default="")
@click.option("--ttl", default=1800, type=click.IntRange(1, 86400))
def prepare_cmd(application: str, work_dir: str, out: str, suite: str, ttl: int) -> None:
    """Prepare a request, then ask the user to Run the target in the IDE."""
    try:
        show(requests.prepare(application, work_dir, out, suite, ttl))
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command("status")
@click.argument("receipt", type=click.Path(exists=True, dir_okay=False))
def status_cmd(receipt: str) -> None:
    """Read request state and any correlated report."""
    show(requests.status(receipt))


@cli.command("wait")
@click.argument("receipt", type=click.Path(exists=True, dir_okay=False))
@click.option("--timeout", default=60.0, type=click.FloatRange(min=0))
def wait_cmd(receipt: str, timeout: float) -> None:
    """Wait for results without managing or terminating a process."""
    result = requests.wait(receipt, timeout)
    show(result)
    if result["timed_out"]:
        sys.exit(4)
    if result["state"] != "completed":
        sys.exit(3)
    sys.exit(_result_exit(result["results"]))


@cli.command("cleanup")
@click.argument("receipt", type=click.Path(exists=True, dir_okay=False))
def cleanup_cmd(receipt: str) -> None:
    """Cancel a pending request or release a completed slot. Keep evidence."""
    try:
        show(requests.cleanup(receipt))
    except (ValueError, OSError) as exc:
        raise click.ClickException(str(exc)) from exc


def _result_exit(results: dict[str, Any]) -> int:
    if results["tests"] == 0 or results["runner_errors"]:
        return 3
    return min(int(results["failures"] + results["errors"]), 2)


@cli.command("run")
@click.argument("exe", type=click.Path(exists=True, dir_okay=False))
@click.option("--application", required=True, help="Application object name, not the EXE name")
@click.option("--work-dir", type=click.Path(exists=True, file_okay=False), default=None)
@click.option("--out", required=True, type=click.Path(dir_okay=False))
@click.option("--suite", default="")
@click.option("--args", "extra", default="", help="Application arguments, not test parameters")
@click.option("--timeout", default=120.0, type=click.FloatRange(min=0))
@click.option("--runtime-version", default=None)
@click.option("--json", "as_json", is_flag=True)
def run_cmd(
    exe: str,
    application: str,
    work_dir: str | None,
    out: str,
    suite: str,
    extra: str,
    timeout: float,
    runtime_version: str | None,
    as_json: bool,
) -> None:
    """Prepare a JSON request, start an EXE, check its exit and matching report.

    Exit codes: 0 pass, 1/2 failed tests (capped), 3 invalid run, 4 timeout.
    """
    directory = Path(work_dir).resolve() if work_dir else Path(exe).resolve().parent
    receipt: str | None = None
    r: run.Run | None = None
    code = 3
    try:
        ticket = requests.prepare(application, directory, out, suite)
        receipt = ticket["receipt"]
        r = run.start(exe, extra, work_dir=directory, runtime_version=runtime_version)
        done = run.wait(r.id, timeout)
        state = requests.status(receipt)
        if as_json:
            show({"process": done, "request": state, "receipt": receipt})
        if done["timed_out"]:
            click.echo("timed out; stopping the driver-owned process", err=True)
            code = 4
        elif done["runtime_error"]:
            click.echo(f"runtime error: {done['runtime_error']}", err=True)
        elif state["state"] != "completed":
            click.echo(f"invalid test run: {state}", err=True)
        else:
            results = state["results"]
            expected = results["failures"] + results["errors"]
            if not as_json:
                click.echo(results["summary"])
            if results["runner_errors"] or done["exit_code"] != expected:
                click.echo(f"inconsistent process exit: {done['exit_code']}", err=True)
            else:
                code = _result_exit(results)
    except (OSError, ValueError) as exc:
        click.echo(str(exc), err=True)
    finally:
        if r is not None:
            try:
                run.stop(r.id)
            except (OSError, ValueError, KeyError) as exc:
                click.echo(f"process cleanup failed: {exc}", err=True)
                if code != 4:
                    code = 3
        if receipt is not None:
            try:
                requests.cleanup(receipt)
            except (OSError, ValueError) as exc:
                click.echo(f"request retained for inspection: {receipt}: {exc}", err=True)
    sys.exit(code)


@cli.command("results")
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
@click.option("--request-id", default=None)
@click.option("--application", default=None)
@click.option("--json", "as_json", is_flag=True)
def results_cmd(path: str, request_id: str | None, application: str | None, as_json: bool) -> None:
    """Validate a JSON report (not the process that produced it)."""
    try:
        data = protocol.report(path, request_id, application)
    except (ValueError, OSError) as exc:
        raise click.ClickException(str(exc)) from exc
    if as_json:
        show(data)
    else:
        click.echo(data["summary"])
    sys.exit(_result_exit(data))


@cli.command("inspect")
@click.argument("exe", type=click.Path(exists=True, dir_okay=False))
@click.option("--args", "extra", default="")
@click.option("--wait", default=3.0, show_default=True)
@click.option("--depth", default=6, show_default=True)
@click.option("--runtime-version", default=None)
def inspect_cmd(exe: str, extra: str, wait: float, depth: int, runtime_version: str | None) -> None:
    """Start an exe, dump its top window's control tree as JSON, stop it."""
    import time

    r = run.start(exe, extra, runtime_version=runtime_version)
    try:
        time.sleep(wait)
        show({"windows": ui.windows(r.id), "controls": ui.controls(r.id, None, None, depth)})
    finally:
        run.stop(r.id)


@cli.command("runtimes")
def runtimes_cmd() -> None:
    """List installed PowerBuilder runtime directories, newest first."""
    for d in run.list_runtime_dirs():
        click.echo(str(d))


@cli.command("serve")
def serve_cmd() -> None:
    """Start the MCP server on stdio."""
    from pb_test_driver.server import run_stdio

    run_stdio()
