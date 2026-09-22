"""pb-test driver: run a PowerBuilder executable and observe it from outside.

Driver functions exposed by the MCP tools in
`server.py` and by the CLI in `cli.py`:

- `run`: start an exe with the PowerBuilder runtime on PATH, wait for it,
  catch the "PowerBuilder application execution error" dialog, stop it.
- `requests` / `protocol`: prepare file requests and validate correlated
  JSON results, including user-started IDE runs without a process handle.
- `junit`: legacy offline XML parser, not used by the JSON run workflow.
- `ui`: enumerate windows and controls through UI Automation, click, type,
  read a DataWindow as rows, take a screenshot.
"""

from __future__ import annotations

__version__ = "0.2.0"
