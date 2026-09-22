# Integrating tests into an existing application

Use the real target's Application object, library list and initialization.
A separate test target is optional; development runs need no EXE build.
Each target registers its suites once in a small adapter. The application
then checks for a request and calls `of_run()` when it is ready.

Make these changes only with approval. Exclude requests and reports from
source control and deployment. Production builds should omit or disable
the hook unless deliberately required. A request grants no permission to
use a database or service.

## Inspect first

Record the target, Application object, PB version, library list, working
directory, approved test environment and default suite. Find where to
check for requests before choosing configuration, where initialization
finishes, and which resources testing must release.

Do not copy an entire Open event into another application. For asynchronous
startup, check early and call `of_run()` from the completion event. Retain
the same adapter instance across those hooks.

## Import the framework

Add the framework and project test libraries to the target. Import these
sources into `pbtest.pbl`, in order:

```text
n_test_listener.sru
n_test_report.sru
n_test_case.sru
n_test_suite.sru
n_test_request.sru
n_test_runner.sru
n_test_options.sru
w_test_setup.srw
w_test_progress.srw
n_test_progress.sru
n_test_session.sru
```

Then import project cases, suites, the adapted `templates/n_test_app.sru`
and the approved Application changes. The adapter must follow its typed
suite dependencies. Use `pb_object_import_file` and read every diagnostic;
do not edit PBLs through another API. For an existing object, export it
with ORCA, edit the exported source, and reimport.

Use matching driver/framework revisions. Native `JSONParser` and
`JSONGenerator`, Windows `MoveFileW` and UTC system time are required.
See [validation](validation.md) for the PB versions actually tested.

## Two calls in the host

Declare an instance variable on the Application, window or controller
that owns the test entry point:

```powerscript
n_test_app inv_tests
```

It is auto-instantiated: no `CREATE` or `DESTROY` is needed. The entry
point, whether Open or another suitable script, is:

```powerscript
if inv_tests.of_requested() then
    // Optional application-specific test initialization.
    inv_tests.of_run()
    return
end if

// Ordinary application startup or action.
```

The service manages request acquisition, suite execution, cleanup hook,
JSON publication and the progress window. It does not halt the application,
close host windows or call `ExitProcess`.

`of_requested()` checks once per instance. The first call captures the
current working directory and acquires `<application>_test.json` there.
Preparing the request must use that directory, even if the call is later
than Open. Subsequent directory changes do not change the acquired paths.

- `false`: no request; continue normally, with no test UI.
- `true`: enter the test branch. This includes rejected or active requests,
  so they cannot accidentally fall through into ordinary startup.
- `of_error()` supplies a rejection diagnostic. If initialization has side
  effects, perform it only when this text is empty. Still call `of_run()`
  to present the rejection without executing a suite.

Keep one adapter instance between detection and execution. Do not copy it
or pass it by value: PowerBuilder copies auto-instantiated NVOs. Use a
`ref` argument if another helper must receive it. A local adapter works
when both calls are in one function; the completed window remains visible
when that local goes out of scope.

`of_run()` is synchronous. It returns the failure/error count, 3 for a
rejected request or failed publication, and -1 when no run was started
(no request, already finished or another run in progress). Repeated and
reentrant calls do not rerun tests. Retained results are available through
`of_finished()`, `of_result()` and `of_summary()`.

An initialization failure before `of_run()` leaves an active request and
no completed report. Stop and inspect it; do not continue normal startup
or fabricate success. Running from an already open UI also requires a
safe test environment: request detection cannot undo earlier production
initialization.

## Let a user start tests interactively

The same adapter can open a response window without an agent-prepared
request. Put the call behind a project-controlled menu, toolbar button,
development screen or other explicit policy:

```powerscript
n_test_app lnv_tests
if lnv_tests.of_interactive() then
    // Optional initialization for this project's test environment.
    lnv_tests.of_run()
end if
```

The setup window lists only suites returned by `of_suite_names()`. The
user selects one, can change the proposed JSON output path, then chooses
Start or Cancel. Start writes and acquires a normal one-shot request in
the current directory. The report uses the same JSON schema as an agent
run. The framework removes its own request control file afterward but
keeps the report. It refuses an existing driver reservation, pending or
active request, and never overwrites a result.

Use a fresh local adapter for each manual invocation, as above. This
allows another run after the previous result window has closed and avoids
reusing completed session state. The process-wide guard still rejects
overlapping or reentrant executions. Keep the local variable in the same
script that calls both methods; auto-instantiated NVOs have value semantics.

`of_interactive()` returns `false` on Cancel. On Start it returns `true`,
then the project can initialize its test environment before `of_run()`.
If setup detects a conflict or invalid request, it also returns `true` so
`of_run()` displays the rejection instead of continuing ordinary business
logic. Check `of_error()` before initialization with side effects.

An already-open application has already performed some initialization.
Only expose this action where that state is safe for tests. If tests need
a distinct database or configuration chosen before normal startup, use
the startup request path or a project-specific restart flow instead.

## Register suites once per target

Adapt `n_test_app`, which inherits from `n_test_session`. Override
`of_suite(string as_name)` to return a newly created, typed suite.
The supplied adapter registers the default and named `n_suite_all` in
`of_suite()` and exposes it to the setup window through `of_suite_names()`.
Keep those two methods in sync. Use distinct adapter names when several targets share a library list.
For more suites, extend its dispatcher, for example:

```powerscript
n_suite_all lnv_all
n_suite_orders lnv_orders
n_test_suite lnv_none
choose case as_name
    case "", "n_suite_all"
        lnv_all = create n_suite_all
        return lnv_all
    case "n_suite_orders"
        lnv_orders = create n_suite_orders
        return lnv_orders
    case else
        SetNull(lnv_none)
        return lnv_none
end choose
```

Expose the same names to manual setup:

```powerscript
as_names[1] = "n_suite_all"
as_names[2] = "n_suite_orders"
```

The orders class is illustrative; import real dependencies first. The
runner owns and destroys the returned suite. An unknown name becomes a
runner error, not a fallback to the default. The runner also verifies the
selected class against a nonempty request. Never use `create using`:
typed references keep cases and suites reachable by the EXE linker.

Override the adapter's `of_cleanup()` for required target cleanup. It
returns an empty string on success, or an error description. Exceptions
are caught and reported. This hook runs before JSON publication, including
on rejection; make it safe for partially initialized resources and release
only resources owned by the test branch. The adapter can call
`of_note("Cleaning up...")` to update progress during cleanup. Do not defer
required cleanup to Application.Close or destructors after publishing a
green report.

## Progress, completion and long tests

In the IDE, `of_run()` opens a nonmodal window before suite selection.
It shows the current case/test, completed/pass/fail/error counts, elapsed
time, a progress bar for the **current case**, and an accumulating result
line for each completed test. Failure and error messages appear inline,
so the finished window is also the run summary. It does not claim an
overall suite percentage: suites can select cases dynamically.

The window updates before and after each test. A long test can provide
cooperative checkpoints through its inherited method:

```powerscript
of_progress("Processed " + String(ll_rows) + " rows")
```

Checkpoints update the message and pump events without changing results.
They do not move the case progress bar until a test finishes. A blocking
SQL call, external call or tight loop without checkpoints can delay
repainting and make the window temporarily unresponsive. This is not a
worker thread or continuous heartbeat. `Yield()` also processes host UI
events; keep unrelated application actions inactive while tests run.
The service guards against reentrant test runs but cannot guard all host
business operations.

Close is disabled during execution, and the window rejects its title-bar
close action. There is no forced cancellation. After cleanup/publication,
the same window shows PASSED, NOT PASSED, Request rejected or Report not
saved, with the summary, request ID and saved report path where available.
Close it when finished; another run requires a fresh request.

The default is no window in an EXE. `of_show_progress(true)` explicitly
opts an interactive EXE into this UI; do not use that override for unattended
runs, since the result window stays open until closed. The IDE default
uses `Handle(GetApplication()) = 0`, as documented in the
[PowerBuilder Handle reference](https://docs.appeon.com/pb2022r3/powerscript_reference/handle_func.html).
Validate the actual IDE experience with the user.

## Lifecycle and post-build execution

The service never terminates its host. A real application's test branch
must decide whether to remain open or end after testing. The standalone
template has no ordinary UI: its IDE result window keeps it open until
closed. Its Close handler reports `of_result()` as the EXE process exit
code, guarded to never exit the IDE. If adapting that policy, keep required
cleanup inside `of_cleanup()`; `ExitProcess` bypasses later destructors.

The CLI expects the EXE to exit and checks the report against its exit
code. Leaving ordinary application windows open is not an unattended
post-build integration. Agree on the host's shutdown/exit policy separately
rather than hiding it in the shared service.

For specialized integrations the lower-level APIs remain available:
`n_test_request.of_acquire()`, then `n_test_runner.of_execute(request,
typed_suite)`, host cleanup and `of_finish(request, cleanup_error)`.
Their caller owns request/runner lifetime and feedback; ordinary targets
should use the adapter rather than reproduce that orchestration in Open.

## Development handoff

1. Import changed sources through ORCA and inspect diagnostics. Do not
   import into running libraries or overwrite unsaved IDE work.
2. Prepare a fresh JSON request for the Application, agreed directory,
   suite and new output path.
3. Ask the user to Run the target or invoke the agreed entry point. Explain
   the progress window and blocking-test limit. They should close the
   finished window and report errors, not launch the same request twice.
4. Wait using the receipt. The agent does not drive or terminate the IDE.
5. Validate correlated JSON and record that IDE process exit was not
   observed. Confirm visible behavior with the user.
6. Release completed requests, retaining evidence. On timeout, ask whether
   execution started or is still busy; never steal an active slot.

After an approved build, use the same protocol in a fresh deployment:

```powershell
pb-test run C:\build\orders.exe --application myapp --work-dir C:\build --suite n_suite_orders --out C:\results\run-002\result.json --runtime-version 22.2
```

Check typed named-suite selection in the EXE, dependencies, runtime,
report and process exit. See [JSON protocol](json-protocol.md) for expiry,
correlation and recovery.
