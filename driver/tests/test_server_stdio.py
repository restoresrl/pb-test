from __future__ import annotations

import asyncio
import sys
from datetime import timedelta
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_stdio_discovery_and_results(tmp_path: Path) -> None:
    report = tmp_path / "report.xml"
    report.write_text(
        '<testsuite name="smoke"><testcase name="pass"/>'
        '<testcase name="fail"><failure>expected failure</failure></testcase></testsuite>',
        encoding="utf-8",
    )

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
                assert {"pb_run_start", "pb_run_results", "pb_ui_read", "pb_run_stop"} <= tools
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
