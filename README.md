# pb-test

Testing for PowerBuilder applications, with PowerScript assertions and a
Python CLI/MCP driver. Tests can run inside an existing application target
or a separate test target.

Both IDE and EXE execution use a one-shot JSON request and a JSON report:

- During development, the agent prepares a request and asks the user to
  run the target in the IDE. No EXE build is required. PowerBuilder still
  compiles the necessary objects.
- After a build, the driver prepares the same request and starts the EXE.
  It also checks process exit, runtime-error dialogs and timeout.

The driver does not build PowerBuilder artifacts. Use the IDE or
[`pb-orca-mcp`](https://github.com/restoresrl/pb-orca-mcp) for that.
[`pb-ai-code`](https://github.com/restoresrl/pb-ai-code) supplies the agent
workflows for setup and use.

## Install

v0.2.0 replaces the v0.1.0 XML protocol with JSON. Framework and driver
must come from the same version; a v0.1.0 driver cannot run these requests.

```powershell
uv tool install "git+https://github.com/restoresrl/pb-test@v0.2.0#subdirectory=driver"
pb-test --version
```

The wheel contains only the driver, not the PowerScript sources or
schemas. Get those from the matching tag's source archive. Updating a
project's framework is a deliberate change, not part of a test run.

The framework was verified on PB 2022 R3 build 3397. Earlier UI checks
also passed on PB 2019 R3 build 2803. See [validation](docs/validation.md)
for what this release actually exercises and what remains unchecked.

## Setup

For an existing application, follow
[Integrating tests into an application](docs/integrating-tests.md).
Each target chooses its own default suite and initialization/cleanup hooks.
The host reads the request early, before opening connections, then runs
the suite when its approved test environment is ready.

For an isolated test application, follow
[Adding a test target](docs/adding-a-test-target.md). The `templates/`
directory includes an Application object, target adapter, target, root
suite and example case. The example deliberately contains a failure and an error.

Import the framework into `pbtest.pbl` in this order:

```text
n_test_listener → n_test_report → n_test_case → n_test_suite
→ n_test_request → n_test_runner → n_test_options → w_test_setup
→ w_test_progress → n_test_progress → n_test_session
```

Import cases and suites next, then the target's `n_test_app` adapter.
PBLs are generated artifacts; keep the `.sru` and `.srw` sources in version
control.

Declare `n_test_app inv_tests` as an instance variable; it is
auto-instantiated. Open, or another approved entry point, needs only:

```powerscript
if inv_tests.of_requested() then
    // Optional target-specific test initialization.
    inv_tests.of_run()
    return
end if
// Normal application startup.
```

The adapter registers typed suites once and can override `of_cleanup()`.
The service manages the request, runner, JSON and IDE progress window,
without closing the host application. Rejected requests also enter the
test branch; check `of_error()` before initialization with side effects.
See the integration guide for asynchronous startup and EXE exit policy.

A menu, toolbar or development-only action can offer manual execution with
no agent and no pre-existing request:

```powerscript
n_test_app lnv_tests
if lnv_tests.of_interactive() then
    // Optional target-specific test initialization.
    lnv_tests.of_run()
end if
```

`of_interactive()` opens a setup window for the typed suite and JSON result
path. Start creates and acquires the same one-shot JSON request used by the
driver. A fresh local adapter permits another manual run after the previous
result window has closed.

## Writing tests

A case inherits from `n_test_case`. Each scripted event named `test_*` is a
test, including inherited events below the framework base class. `setup`
and `teardown` run around each test. The case instance is reused, so reset
state in those hooks. Assertions collect failures without stopping the
script:

```text
event test_lower;of_assert_equal("hello", Lower("HELLO"), "Lower")
of_assert_true(Pos("hello", "ell") = 2, "Pos finds the substring")
end event
```

`of_assert_equal` supports string, long, decimal, double, boolean, date
and datetime. `of_assert_true`, `of_assert_false`, `of_assert_null`,
`of_assert_not_null` and `of_fail` complete the set. Runtime exceptions
inside tests are reported as errors. Expected exceptions must be caught
and checked by the test itself.

Suites inherit from `n_test_suite` and list typed cases in `ue_execute`:

```text
event ue_execute;n_test_strings lnv_strings
lnv_strings = create n_test_strings
of_run_case(lnv_strings)
end event
```

Suites destroy the cases passed to them and can nest other suites with
`of_run_suite`. The host maps requested names to typed suite instances;
the runner checks that the supplied class matches the request. It never
instantiates a class from a string. Typed references keep the suite and
cases reachable by the linker. The sample registers only `n_suite_all`;
add a typed branch in the adapter's `of_suite()` for each additional
selectable suite.
Selection is per suite, not per test event.

## Run from the IDE

Use the actual startup directory configured for this target:

```powershell
pb-test prepare --application myapp --work-dir C:\project --suite n_suite_orders --out C:\results\run-001\result.json
```

Keep the returned `receipt` path. The agent now asks the user to run the
target in the IDE. A progress window shows the running test, counts, current-case progress
and an accumulating PASS/FAIL/ERROR line for every completed test, then
the outcome and report path. Close it when
finished. Long tests can call `of_progress("message")` at cooperative
checkpoints; blocking calls can still delay repainting. The agent does
not start, automate or terminate the IDE. EXE runs have no window by
default.

```powershell
pb-test wait C:\results\run-001\result.json.request.json --timeout 60
pb-test cleanup C:\results\run-001\result.json.request.json
```

A timeout does not cancel a request. Cleanup can cancel a pending request
or release a completed slot; it refuses to remove an active request.

## Run a built application

```powershell
pb-test run C:\build\orders.exe --application myapp --runtime-version 22.2 --suite n_suite_orders --out C:\results\run-002\result.json
```

`--application` is the Application object name, which may differ from the
EXE name. The default working directory is the EXE directory; use
`--work-dir` if the application needs another startup directory. The
request is prepared there, without changing the application's normal
arguments. Omit `--suite` for the target's default suite.

The driver preserves existing reports and deployments. Every attempt
needs a fresh output path. `--json` includes both process observations and
correlated results. CLI exit codes: 0 pass, 1/2 failed tests (capped),
3 invalid run, 4 timeout. See the [protocol](docs/json-protocol.md) for
validation rules, crash recovery and migration from v0.1.0.

## MCP

Start the server with `pb-test serve`. Register a locally installed driver:

```json
{
  "mcpServers": {
    "pb-test": { "command": "pb-test", "args": ["serve"] }
  }
}
```

| Tool | Purpose |
| --- | --- |
| `pb_test_prepare` | Reserve a target slot and publish a JSON request; return a receipt |
| `pb_test_status`, `pb_test_wait` | Inspect/wait for the matching result, including user-started IDE runs |
| `pb_test_cleanup` | Cancel pending or release completed requests; retain reports |
| `pb_run_start` | Start an EXE with its runtime; use the prepared request's working directory |
| `pb_run_wait` | Observe exit, runtime dialog or timeout |
| `pb_run_stop`, `pb_run_list` | Stop/list driver-owned processes, not IDE runs |
| `pb_run_results` | Validate a JSON report; does not certify process exit |
| `pb_ui_windows`, `pb_ui_controls` | Enumerate windows and controls |
| `pb_ui_read`, `pb_ui_click`, `pb_ui_type` | Read values and interact with controls |
| `pb_ui_screenshot`, `pb_ui_close` | Save a human-facing image or close a window |

For an IDE run: prepare, ask the user to Run, wait, inspect, cleanup.
For an EXE run: prepare, start, wait for the process, inspect the request
result, stop any remaining process, cleanup. A green report alone cannot
certify a crash-free EXE run.

## UI and runtime limits

UI tools are independent of the test framework and still require an EXE
started by the driver and an interactive Windows desktop. They do not
automatically attach to the IDE.

- The driver enables `[Application] ACCESSIBILITY=1` in `pb.ini` beside
  the EXE by default. This can rewrite INI formatting/comments; use a
  disposable deployment or disable the option when already configured.
- Deploy `pbacc.dll` and `PBAccessibility.dll` with the runtime when
  required for UI Automation.
- DataWindow values are formatted strings. `rows` are visual groups,
  not logical records (`rows_are_logical=false`). Off-screen cells and
  untested styles are not guaranteed. Reread values after editing.
- Runtime-error dialogs are detected with Win32, not UI Automation.
- The EXE's runtime XML can override PATH. Conflicts with an explicit
  runtime selection are rejected, not silently rewritten.
- Tests are not a sandbox. Agree on database and service access before
  startup; the framework does not provide rollback or isolation.

## Licence

MIT. See [LICENSE](LICENSE).
