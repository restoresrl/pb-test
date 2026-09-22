from __future__ import annotations

import asyncio
import sys
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_stdio_discovery_and_results(
    tmp_path: Path, write_report: Callable[..., dict[str, Any]]
) -> None:
    report = tmp_path / "report.json"
    write_report(report, statuses=("pass", "fail"))

    async def check() -> None:
        parameters = StdioServerParameters(
            command=sys.executable, args=["-m", "pb_test_driver", "serve"]
        )
        async with stdio_client(parameters) as (reader, writer):
            async with ClientSession(
                reader, writer, read_timeout_seconds=timedelta(seconds=30)
            ) as client:
                await client.initialize()
                tools = {tool.name for tool in (await client.list_tools()).tools}
                assert {
                    "pb_run_start",
                    "pb_run_results",
                    "pb_ui_read",
                    "pb_run_stop",
                    "pb_test_prepare",
                    "pb_test_status",
                    "pb_test_wait",
                    "pb_test_cleanup",
                } <= tools
                prepared = await client.call_tool(
                    "pb_test_prepare",
                    {
                        "application": "sample",
                        "work_dir": str(tmp_path),
                        "out": str(tmp_path / "ide.json"),
                    },
                )
                assert not prepared.isError
                assert prepared.structuredContent is not None
                receipt = prepared.structuredContent["receipt"]
                pending = await client.call_tool("pb_test_wait", {"receipt": receipt, "timeout": 0})
                assert pending.structuredContent is not None
                assert pending.structuredContent["timed_out"] is True
                released = await client.call_tool("pb_test_cleanup", {"receipt": receipt})
                assert not released.isError
                result = await client.call_tool("pb_run_results", {"path": str(report)})
                assert not result.isError
                assert result.structuredContent is not None
                assert result.structuredContent["tests"] == 2
                assert result.structuredContent["failures"] == 1
                missing = await client.call_tool(
                    "pb_run_results", {"path": str(tmp_path / "missing")}
                )
                assert missing.isError

    asyncio.run(check())
