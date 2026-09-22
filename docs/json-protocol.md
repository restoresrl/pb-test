# JSON requests and results (version 1)

The same file request starts suites in a user-run IDE target and a
built EXE. There is no test command-line protocol. The host application
must include the framework and read requests at an agreed entry point.
The Application object name need not match the EXE name.

See [request schema](../schemas/request.schema.json) and
[result schema](../schemas/result.schema.json). Schema version 1 is
independent of the package version. Both files use UTF-8; readers accept
an optional BOM. Reports from PowerBuilder include a BOM.

## Request

The application reads `<lowercase-application-class>_test.json` in its
current working directory, captured when `n_test_request.of_acquire()`
runs, normally through the adapter's first `of_requested()` call.
Identity comes from `ClassName(GetApplication())`, not the EXE stem or a
mutable display name. Check before initialization changes directories;
for a later entry point, agree on its directory before preparing the
request. Do not assume the current directory is the PBT folder.
Different applications have separate slots; two checkouts of the same
application must use different working directories.

```json
{
  "schema_version": 1,
  "request_id": "f41056d46c90491d82961b12f5b2f1a1",
  "application": "myapp",
  "suite": "n_suite_ordini",
  "output": "results/f41056d46c90491d82961b12f5b2f1a1/result.json",
  "expires_at": 1893456000
}
```

This is an example, not a request to leave in a deployment. Agent and
CLI runs use the prepare tool to generate a fresh ID and expiry. A target
may expose `n_test_session.of_interactive()` through a project-controlled
action; its setup window creates and immediately acquires the same JSON
shape without requiring the driver. `expires_at` is an integer
UTC Unix timestamp. Expiry limits acquisition, not how long tests may run.
The driver defaults to 30 minutes and allows up to 24 hours.

`application` and `suite` use lowercase PB identifiers. `suite` is
optional (or empty) to select the host's typed default suite. Only suites
can be selected, not individual test events. The host maps names to typed suite instances and passes the
selected instance to the runner. The runner rejects a class/name mismatch;
it does not dynamically create test objects from strings.

The output's parent directory must already exist. Relative output paths
resolve against the request's startup directory, even if initialization
later changes the working directory. Use ordinary drive-qualified or UNC
paths for absolute paths. The driver always writes an absolute path and
creates its parent directory. It never reuses an existing output path.

Unknown fields, missing required fields, wrong types, unsupported versions,
wrong application, invalid JSON and expired requests block test startup.
The host must not fall back to ordinary startup after rejection. The
framework retains the request and writes a JSON error diagnostic beside
it when possible. Malformed requests cannot reliably supply an output
path or request ID; their diagnostics are not completed test reports.

## Lifecycle and concurrency

1. `pb_test_prepare` reserves `<app>_test.json.lock` with exclusive directory
   creation and an `owner.json` inside it. Cleanup checks this ID before
   releasing a reservation, so an old receipt cannot release a newer run.
   It writes an immutable receipt next to the output, named
   `<output>.request.json`, then publishes the complete pending request.
   The receipt contains the request and its absolute control-file path.
2. PowerBuilder acquires a request by renaming it to
   `<app>_test.json.active` with Windows `MoveFileW`, without replacement.
   Two launches cannot both acquire the same file. An existing active
   file blocks another launch; a missing pending file means normal startup.
3. The host executes tests and performs its required cleanup. Only then
   does `of_finish` write `<output>.tmp`, close it and rename it to the final
   output. Readers must ignore temporary files. An existing output or
   temporary file blocks publication rather than overwriting evidence.
4. `pb_test_status` or `pb_test_wait` uses the receipt to correlate the
   report ID, application and requested suite. A completed report includes
   the actual suite as well. Status survives MCP server restarts because
   it does not depend on the driver's process registry.
5. `pb_test_cleanup` releases a completed request's control files and lock,
   leaving its receipt and report. It can also cancel a pending or expired
   request by racing the application's acquisition rename. If acquisition
   wins, cancellation fails and must not stop the application.

Keep one request per application/start-directory slot. An external
producer must use prepare; the framework's interactive setup refuses a
driver lock or existing request. Manually writing files bypasses reservation
and freshness checks. Do not edit a request after preparation.

`pending`, `active`, `completed`, `expired`, `rejected`, `invalid`,
`conflict` and `missing` are request states, not test verdicts. `completed`
can contain failed tests. A wait timeout adds `timed_out=true` without
changing or cancelling the request. A second launch while active writes
an error diagnostic; it must not run the same tests again.

Cleanup refuses active, rejected, invalid, conflicting or missing requests.
For crash recovery, first establish with the user that the target is no
longer running. Preserve request, diagnostic and any temporary report in
the evidence directory; then remove only that slot's control files and
lock directory (including its owner marker) with explicit approval. Never remove an active IDE
request merely because an agent wait expired. Preparation/publication
failures can leave a receipt or a temporary file for inspection.

Use local Windows filesystems for the request and report. Remote shares,
synchronization clients and crash durability across power loss are not
part of the validation. No filesystem protocol prevents a local user
from deliberately forging a report. These files are not an authentication
boundary or a database sandbox.

## Result

```json
{
  "schema_version": 1,
  "request_id": "f41056d46c90491d82961b12f5b2f1a1",
  "application": "myapp",
  "requested_suite": "n_suite_ordini",
  "suite": "n_suite_ordini",
  "completed": true,
  "tests": 1,
  "passed": 1,
  "failures": 0,
  "errors": 0,
  "runner_errors": [],
  "cases": [
    {
      "suite": "n_suite_ordini",
      "classname": "n_test_totali",
      "name": "test_totale",
      "status": "pass",
      "message": "",
      "time": 0.001
    }
  ]
}
```

A failure is an assertion mismatch; an error is an exception. Messages
retain line breaks and Unicode. `time` is elapsed `Cpu()` milliseconds
converted to seconds, not a benchmarking guarantee. `runner_errors`
records failures outside an individual test, including host cleanup errors
passed to `of_finish`. Failure to publish means there is no completed
report, even if every assertion ran.

The driver checks types, status values, finite nonnegative durations,
counts against the cases, and correlation. It adds `ok` and `summary` to
its response; it does not trust a producer-supplied `ok` flag. At least
one executed test, no failures/errors and no runner errors are needed
for `ok=true`. This certifies the reported test execution only.

For an IDE run, record that process exit and runtime dialogs were not
observed by the driver. Ask the user about errors outside the recorded
execution. The framework report covers only the agreed execution and
cleanup boundary; do not claim whole-application health.

For an EXE run, additionally require no timeout or runtime dialog and an
exit code consistent with the failed plus errored test count. Zero tests,
missing/invalid/stale reports, runner errors and inconsistent process
outcomes block validation. CLI exit codes are 0 for pass, 1/2 for failed
or errored tests (capped), 3 for invalid execution, and 4 for timeout.

## Migration from 0.1

Upgrade framework and driver together. `of_run_from_commandline` has been
replaced by the target adapter's `of_requested()` and `of_run()` methods.
The lower-level acquire/execute/finish APIs remain available. Register
alternative suite names in the adapter's typed `of_suite()` dispatcher;
the runner no longer uses
`create using`. `/suite`, `/out` and `/exit` no longer configure execution. The CLI requires `--application` and a
fresh `--out` JSON path. `pb_run_results` reads JSON, not JUnit XML.
Old reports remain evidence; do not rename XML files to `.json`.

Interactive runs do not create driver receipts. The framework removes
only the pending/active control file it created after execution and keeps
the JSON report. Driver-prepared runs retain their control files for
receipt-based status and cleanup.

The Python JUnit parser remains an offline legacy helper for old reports;
the request runner never calls it. The PowerScript XML serializer has been
removed. No implicit fallback to XML exists. A CI service that only accepts
JUnit needs an explicit conversion step; JSON is the native result.

The EXE's runtime XML (`RuntimePath`) is unrelated and remains unchanged.
The JSON workflow arrived in v0.2.0. A v0.1.0 driver cannot read these
requests. Update the framework sources in the project's PBLs and the
installed driver in the same change.
