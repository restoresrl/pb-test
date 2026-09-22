"""MCP server: one tool per driver function.

Tool results are plain dicts so the agent reads structured text. A runtime error
dialog is data in `pb_run_wait`, not an exception.
"""

from __future__ import annotations

from typing import Any

from pb_test_driver import protocol, requests, run, ui


def build_server() -> Any:
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("pb-test")

    @mcp.tool()
    def pb_run_start(
        exe: str,
        args: str = "",
        work_dir: str | None = None,
        runtime_version: str | None = None,
        runtime_dir: str | None = None,
        accessibility: bool = True,
    ) -> dict[str, Any]:
        """Start a PowerBuilder exe with the runtime on PATH. Returns a run_id.

        `runtime_version` is the runtime the exe was built with, e.g. "22.2"; the
        executable XML RuntimePath is used when omitted, else the newest runtime.
        A conflict between that XML and an explicit request fails before launch.
        The driver does not verify every loaded DLL. `accessibility` writes
        `[Application] ACCESSIBILITY=1` into pb.ini next to the exe so the UI tools
        can see DataWindow contents. For suites call pb_test_prepare first,
        then launch using the same work_dir. No test command-line switches are needed.
        """
        r = run.start(exe, args, work_dir, runtime_version, runtime_dir, accessibility)
        return r.info()

    @mcp.tool()
    def pb_run_wait(
        run_id: str, timeout: float = 60.0, dismiss_error: bool = True
    ) -> dict[str, Any]:
        """Wait for exit, a runtime error dialog, or the timeout.

        `runtime_error` (title, text with event/object/line, R-code) is filled when
        the "PowerBuilder application execution error" dialog showed. `exit_code`
        of a pb-test target is the number of failed plus errored tests.
        """
        return run.wait(run_id, timeout, dismiss_error)

    @mcp.tool()
    def pb_run_stop(run_id: str) -> dict[str, Any]:
        """Kill the process of a run."""
        return run.stop(run_id)

    @mcp.tool()
    def pb_run_list() -> list[dict[str, Any]]:
        """Runs started in this server session and their state."""
        return run.runs()

    @mcp.tool()
    def pb_run_results(
        path: str, request_id: str | None = None, application: str | None = None
    ) -> dict[str, Any]:
        """Validate a completed JSON report. Does not certify process exit.

        Prefer pb_test_status with the receipt to check request correlation.
        """
        return protocol.report(path, request_id, application)

    @mcp.tool()
    def pb_test_prepare(
        application: str, work_dir: str, out: str, suite: str = "", ttl: int = 1800
    ) -> dict[str, Any]:
        """Reserve a target and publish its one-shot JSON request.

        application is the Application object, not necessarily the EXE stem.
        work_dir must be the actual startup directory. For IDE runs ask the
        user to press Run after this call. For EXE runs use pb_run_start next.
        """
        return requests.prepare(application, work_dir, out, suite, ttl)

    @mcp.tool()
    def pb_test_status(receipt: str) -> dict[str, Any]:
        """Read request state and correlated JSON results, without a process handle."""
        return requests.status(receipt)

    @mcp.tool()
    def pb_test_wait(receipt: str, timeout: float = 60.0) -> dict[str, Any]:
        """Wait for IDE or EXE test results. Timeout never kills or cancels a run."""
        return requests.wait(receipt, timeout)

    @mcp.tool()
    def pb_test_cleanup(receipt: str) -> dict[str, Any]:
        """Cancel an unclaimed request or release a completed slot; retain evidence.

        Refuses active, invalid and missing requests. Never stops the IDE.
        """
        return requests.cleanup(receipt)

    @mcp.tool()
    def pb_ui_windows(run_id: str) -> list[dict[str, Any]]:
        """Top-level windows of the run, including a runtime error dialog if showing."""
        return ui.windows(run_id)

    @mcp.tool()
    def pb_ui_controls(
        run_id: str,
        window: str | None = None,
        selector: dict[str, Any] | None = None,
        depth: int = 6,
    ) -> list[dict[str, Any]]:
        """Control tree of a window as a flat list with `level`.

        `window` is an exact title, `re:<regex>`, or omitted for the top window.
        `selector` narrows to a control: keys auto_id, title, title_re,
        control_type, class_name, found_index. auto_id is the PowerBuilder control
        id (1000, 1001, ...); title is accessiblename or text.
        """
        return ui.controls(run_id, window, selector, depth)

    @mcp.tool()
    def pb_ui_read(
        run_id: str, window: str | None = None, selector: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Read formatted values, labels and cell rectangles.

        DataWindow `rows` groups cells by rectangle top, not logical record.
        `rows_are_logical=false`; use `cells` for freeform and other layouts.
        Off-screen cells and untested styles are not guaranteed.
        """
        return ui.read(run_id, window, selector)

    @mcp.tool()
    def pb_ui_click(
        run_id: str, selector: dict[str, Any], window: str | None = None, method: str = "invoke"
    ) -> dict[str, Any]:
        """Click a control: `invoke` (UIA pattern) or `mouse`."""
        return ui.click(run_id, window, selector, method)

    @mcp.tool()
    def pb_ui_type(
        run_id: str,
        selector: dict[str, Any],
        text: str,
        window: str | None = None,
        method: str = "auto",
        clear: bool = True,
        tab_out: bool = False,
    ) -> dict[str, Any]:
        """Type into an edit control or a DataWindow cell.

        `auto` uses the keyboard directly for DataWindow cells. Ordinary edits
        try ValuePattern with keyboard fallback. Text is literal, not key syntax.
        Set `tab_out` to accept the cell and reread its value to verify the edit.
        """
        return ui.type_text(run_id, window, selector, text, method, clear, tab_out)

    @mcp.tool()
    def pb_ui_screenshot(
        run_id: str, path: str, window: str | None = None, selector: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Save a PNG of a window or control. Use it to show a human, not to read values."""
        return ui.screenshot(run_id, path, window, selector)

    @mcp.tool()
    def pb_ui_close(run_id: str, window: str | None = None) -> dict[str, Any]:
        """Close a window through its title bar, the way a user would."""
        return ui.close_window(run_id, window)

    return mcp


def run_stdio() -> None:
    build_server().run(transport="stdio")
