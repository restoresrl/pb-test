# pb-test driver

Run PowerBuilder test executables, read their JUnit reports and inspect
windows through UI Automation. The driver provides an MCP server and a
CLI. It does not build PBLs or executables.

## Install and run

Install the pinned release:

```powershell
uv tool install "git+https://github.com/restoresrl/pb-test@v0.1.0#subdirectory=driver"
pb-test --version
pb-test run C:\proj\test_myapp.exe --runtime-version 22.2
pb-test serve
```

You can also install a built `pb_test_driver-0.1.0-py3-none-any.whl`.
The Python wheel contains the driver, not the PowerScript framework.
Download the source archive from
[v0.1.0](https://github.com/restoresrl/pb-test/releases/tag/v0.1.0) for
`framework/`, `templates/` and `docs/adding-a-test-target.md`. Use those
files to build a test target with ORCA or the IDE. From a local
checkout, `uv tool install ./driver` installs the Python package.

The runtime needs to be installed or deployed on Windows. UI actions
need an interactive desktop. The driver reads `RuntimePath` from the
executable's adjacent XML file and rejects a conflict with an explicit
runtime selection before starting the process. Otherwise it puts the
selected runtime on PATH. This does not verify every DLL the Windows
loader will select.

By default, starting a run enables accessibility in `pb.ini` next to
the executable. Use a disposable test deployment: updating an existing
INI preserves parsed settings, but may change formatting and comments.
MCP callers can set `accessibility=false` to leave that file alone.

## Results and limits

`pb-test run` exits 0 only with executed, passing tests and process exit
code 0. Failed or errored tests return their count, capped at 2. A
runtime error, missing report or inconsistent passing result returns 3;
a timeout returns 4. The CLI stops its child process before returning.
MCP callers must stop any run still alive after `pb_run_wait`.

`pb_ui_read` exposes formatted cell values and their rectangles.
Its `rows` field groups cells by vertical position. These are visual
groups, not logical DataWindow rows: freeform layouts split one record
across several groups. `rows_are_logical=false` states that limit;
`cells` retains the individual observations. Off-screen cells and other
presentation styles have not been validated.

The framework and driver have been tested together on PB 2022 R3 build
3397. UI reading, editing and runtime-error detection also passed on
PB 2019 R3 build 2803. PB 2025 R2 remains unverified because the ORCA
session could not load its DLL in the test environment.

## MCP configuration

```json
{
  "mcpServers": {
    "pb-test": { "command": "pb-test", "args": ["serve"] }
  }
}
```

Tools cover process start/wait/stop, JUnit parsing, window/control
inspection, click, text entry and screenshots. Runtime-error dialogs
come back as structured data, including the R-code and message.
