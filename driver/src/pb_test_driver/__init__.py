"""pb-test driver: run a PowerBuilder executable and observe it from outside.

Three groups of functions, mirrored one-to-one by the MCP tools in
`server.py` and by the CLI in `cli.py`:

- `run`: start an exe with the PowerBuilder runtime on PATH, wait for it,
  catch the "PowerBuilder application execution error" dialog, stop it.
- `junit`: read the result file written by the `n_test_runner` object of
  the PowerScript framework.
- `ui`: enumerate windows and controls through UI Automation, click, type,
  read a DataWindow as rows, take a screenshot.
"""

from __future__ import annotations

__version__ = "0.1.0"
