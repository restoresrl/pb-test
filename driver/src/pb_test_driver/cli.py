"""`pb-test` command line: run a test target, read results, serve MCP."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from pb_test_driver import __version__, junit, run, ui


@click.group()
@click.version_option(__version__, prog_name="pb-test")
def cli() -> None:
    """Run and observe PowerBuilder executables."""


@cli.command("run")
@click.argument("exe", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--out",
    "out",
    type=click.Path(dir_okay=False),
    default=None,
    help="JUnit XML path passed as /out=. Default: <exe dir>/<exe>.test.result.xml",
)
@click.option(
    "--suite", default=None, help="Suite class passed as /suite= (needs a PBD or PBR, see README)"
)
@click.option("--args", "extra", default="", help="Extra command line for the exe")
@click.option(
    "--timeout", default=120.0, show_default=True, help="Seconds before the run is killed"
)
@click.option(
    "--runtime-version",
    default=None,
    help='Runtime on PATH, e.g. "22.2". Default: XML RuntimePath, else newest installed',
)
@click.option("--json", "as_json", is_flag=True, help="Print the parsed results as JSON")
def run_cmd(
    exe: str,
    out: str | None,
    suite: str | None,
    extra: str,
    timeout: float,
    runtime_version: str | None,
    as_json: bool,
) -> None:
    """Run a pb-test target and print its summary.

    Exit code: failed + errored tests (capped at 2), 3 on a runtime error, 4 on timeout.
    """
    exe_path = Path(exe).resolve()
    out_path = Path(out).resolve() if out else exe_path.parent / f"{exe_path.stem}.test.result.xml"
    if out_path.exists():
        out_path.unlink()
    args = f'/out="{out_path}" /exit'
    if suite:
        args += f" /suite={suite}"
    if extra:
        args += " " + extra
    r = run.start(exe_path, args, runtime_version=runtime_version)
    try:
        done = run.wait(r.id, timeout)
    finally:
        run.stop(r.id)
    if done["timed_out"]:
        click.echo(f"timed out after {timeout}s; process killed", err=True)
        sys.exit(4)
    if done["runtime_error"]:
        click.echo(
            f"runtime error: {done['runtime_error']['title']}\n{done['runtime_error']['text']}",
            err=True,
        )
        sys.exit(3)
    if not out_path.exists():
        click.echo(
            f"the target exited with code {done['exit_code']} but wrote no {out_path}", err=True
        )
        sys.exit(3)
    results = junit.parse_file(out_path)
    if results.tests == 0 or (results.ok and done["exit_code"] != 0):
        click.echo(
            f"invalid test run: exit code {done['exit_code']}, {results.tests} tests; "
            "a passing run needs executed tests and exit code 0",
            err=True,
        )
        sys.exit(3)
    if as_json:
        click.echo(json.dumps(results.to_dict(), indent=2))
    else:
        click.echo(results.summary())
    sys.exit(min(results.failures + results.errors, 2))


@cli.command("results")
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
@click.option("--json", "as_json", is_flag=True)
def results_cmd(path: str, as_json: bool) -> None:
    """Print a JUnit XML result file."""
    results = junit.parse_file(path)
    click.echo(json.dumps(results.to_dict(), indent=2) if as_json else results.summary())
    sys.exit(0 if results.ok else 1)


@cli.command("inspect")
@click.argument("exe", type=click.Path(exists=True, dir_okay=False))
@click.option("--args", "extra", default="")
@click.option("--wait", default=3.0, show_default=True, help="Seconds to wait for the first window")
@click.option("--depth", default=6, show_default=True)
@click.option("--runtime-version", default=None)
def inspect_cmd(exe: str, extra: str, wait: float, depth: int, runtime_version: str | None) -> None:
    """Start an exe, dump its top window's control tree as JSON, stop it."""
    import time

    r = run.start(exe, extra, runtime_version=runtime_version)
    try:
        time.sleep(wait)
        click.echo(
            json.dumps(
                {"windows": ui.windows(r.id), "controls": ui.controls(r.id, None, None, depth)},
                indent=2,
            )
        )
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
