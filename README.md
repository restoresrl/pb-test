# pb-test

Testing for PowerBuilder applications, built to be driven by a coding
agent through MCP. Two halves:

- `framework/`: four PowerScript objects (`n_test_case`, `n_test_suite`,
  `n_test_runner`, `n_test_report`) that run xUnit-style tests inside a
  PowerBuilder test application and write a JUnit XML result file.
- `driver/`: a Python package that starts the executable with the right
  runtime, catches the "application execution error" dialog, parses the
  results, and drives windows and DataWindows through UI Automation.
  It is an MCP server first and a command line second.

`pb-test` sits next to [`pb-orca-mcp`](https://github.com/restoresrl/pb-orca-mcp),
which builds the PBLs and the exe, and is orchestrated by the `pb-test`
skill of [`pb-ai-code`](https://github.com/restoresrl/pb-ai-code). It works
without either: the framework is plain PowerScript, the driver a plain CLI.

The framework and driver are verified together on PB 2022 R3 build
3397. UI reading, editing and runtime-error detection also passed on
PB 2019 R3 build 2803, with the loaded runtime DLL checked. PB 2025 R2
is unverified: its ORCA DLL failed to load in the test environment.

## Install

```powershell
uv tool install "git+https://github.com/restoresrl/pb-test@v0.1.0#subdirectory=driver"
pb-test --version
```

The Python wheel contains only the driver. Download the source archive
from [v0.1.0](https://github.com/restoresrl/pb-test/releases/tag/v0.1.0)
or clone that tag for the PowerScript sources and templates. Build the
framework PBL from source
with ORCA as described in [`docs/adding-a-test-target.md`](docs/adding-a-test-target.md),
or import the four `.sru` files into a `pbtest.pbl` in the IDE.

## Writing a test

A test case is a nonvisual object inherited from `n_test_case`. Every
event whose name starts with `test_` and has a script is a test; `setup`
and `teardown` run around each one. Assertions collect failures and let
the test continue:

```text
event test_lower;of_assert_equal("hello", Lower("HELLO"), "Lower")
of_assert_true(Pos("hello", "ell") = 2, "Pos finds the substring")
end event
```

`of_assert_equal` is overloaded for string, long, decimal, double,
boolean, date and datetime. `of_assert_true`, `of_assert_false`,
`of_assert_null`, `of_assert_not_null` and `of_fail` complete the set.
A runtime error inside a test is caught and reported as an error with
the event, object and line.

A suite is inherited from `n_test_suite` and lists its cases in
`ue_execute`, one typed variable each:

```text
event ue_execute;n_test_strings lnv_strings
lnv_strings = create n_test_strings
of_run_case(lnv_strings)
end event
```

The typed variable matters. PowerBuilder links into the executable only
the objects that are referenced statically; a class named only in a
string is pruned, and `create using` fails at runtime with "Cannot find
data type". Suites can run other suites with `of_run_suite`.

The test application's `open` event creates the runner and hands it the
root suite. `templates/` has a ready-made application object, suite and
example case.

## Running

```powershell
pb-test run C:\proj\test_myapp.exe --runtime-version 22.2
```

That starts the exe with `/out=<path> /exit`, waits, and prints:

```text
n_suite_all: 5 tests, 3 passed, 1 failed, 1 errors
FAIL n_test_example.test_that_fails: this assertion is meant to fail: expected 'expected' but was 'actual'
ERROR n_test_example.test_that_raises: Null object reference at line 3 in test_that_raises event of object n_test_example.
```

The exit code is the number of failed plus errored tests, capped at 2.
A runtime error outside a test exits 3 with the dialog text; a timeout
exits 4. A run with no executed tests, or passing XML with a nonzero
process exit, also exits 3. Inside the IDE, run the test target and the
runner shows the same summary in a message box.

Command line switches the test application understands:

| Switch | Meaning |
| --- | --- |
| `/out=<path>` | Where to write the JUnit XML. Default `<appname>.test.result.xml` in the current directory. |
| `/suite=<class>` | Run this suite instead of the default. Only works when the class survived the link (PBD or PBR). |
| `/exit` | Set the process exit code to the failure count and skip the message box. |

## MCP server

```powershell
pb-test serve
```

| Tool | Does |
| --- | --- |
| `pb_run_start` | Start an exe with the runtime on PATH and `ACCESSIBILITY=1` in `pb.ini`. Returns a `run_id`. |
| `pb_run_wait` | Wait for exit, a runtime error dialog, or a timeout. The dialog text comes back as data. |
| `pb_run_stop`, `pb_run_list` | Kill a run; list runs. |
| `pb_run_results` | Parse a JUnit XML file. |
| `pb_ui_windows` | Top-level windows, including a runtime error dialog if showing. |
| `pb_ui_controls` | Control tree of a window: type, name, `auto_id` (the PB control id), rectangle. |
| `pb_ui_read` | Formatted values, labels and cell rectangles. `rows` groups cells by vertical position, not logical record. |
| `pb_ui_click` | Invoke pattern or mouse click. |
| `pb_ui_type` | ValuePattern for ordinary edits; keyboard input for DataWindow cells. |
| `pb_ui_screenshot` | PNG of a window or control. |
| `pb_ui_close` | Close a window through its title bar. |

Register it next to `pb-orca-mcp` in the client's MCP configuration:

```json
{
  "mcpServers": {
    "pb-test": { "command": "pb-test", "args": ["serve"] }
  }
}
```

## What the driver relies on

- UI Automation is off by default. `pb_run_start` writes
  `[Application] ACCESSIBILITY=1` into `pb.ini` next to the exe. Without it
  a DataWindow is an empty pane.
- `pbacc.dll` and `PBAccessibility.dll` from the runtime directory have to
  ship with a deployed application for the same tools to work there.
- The runtime error dialog is found through the win32 backend. UI
  Automation does not list it.
- `<exe>.xml` can select the runtime through `RuntimePath`, overriding
  PATH. The driver rejects conflicts with an explicit runtime request
  and does not rewrite this file. Check it in each test deployment.
- DataWindow `rows` are visual groups. Freeform fields from one record
  can occupy several groups; `rows_are_logical=false` and the raw
  `cells` make that limitation explicit. Do not infer record counts.
- Build to a new location and replace an old deployment only after
  success. pb-orca-mcp v0.2.9 supplies an icon and per-library flags
  and rejects existing outputs without changing them. For v0.2.8,
  pass both arguments explicitly as described in
  `docs/adding-a-test-target.md`.

## Licence

MIT. See [LICENSE](LICENSE).
