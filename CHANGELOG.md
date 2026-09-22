# Changelog

## 0.2.0 - 2026-09-22

Breaking change: upgrade framework and driver together. A v0.1.0 driver
cannot run these requests, and this driver cannot read a v0.1.0 host.

- Add the auto-instantiated `n_test_session` and target adapter template:
  check `of_requested()`, initialize the host, then call `of_run()`.
  Register typed suites and required cleanup once in the adapter.
- Add an IDE progress window with current test, counts, current-case bar
  and an accumulating PASS/FAIL/ERROR summary with messages and durations.
  Long tests can emit cooperative checkpoints; blocking calls can still
  delay repainting. EXEs stay silent by default. The service neither exits
  nor closes its host and rejects reentrant runs.
- Add `of_interactive()` to the same target adapter. A project-controlled
  menu or button can open suite/output setup and create the same one-shot
  JSON request without an agent. Manual runs preserve reports and clean up
  only the request control file they created.
- Keep progress observation in a separate reference-type object, avoiding
  PowerBuilder's auto-instantiated object copying. Include empty-suite
  and host-cleanup errors in the runner summary.
- Capture UI click metadata before invoking controls that may close their
  window or exit the process.
- Replace the test execution protocol with versioned JSON requests and
  reports. Prepare, inspect, wait and cleanup tools support user-started
  IDE sessions without an EXE build, and post-build EXE runs with the same
  request file. Receipts correlate reports across driver restarts.
- Add `n_test_request` for one-shot acquisition, expiry and rejection
  diagnostics. Split runner execution from report publication so hosts
  can initialize and clean up their own environment. The runner no longer
  calls `ExitProcess`. Hosts map suite names to typed instances; the
  runner rejects mismatches instead of using `create using`.
- Update the host template, integration guides, CLI/MCP documentation and
  protocol schemas. Separate-target setup is optional.
- Preserve existing outputs, retain active requests on timeout, and reject
  mismatched IDs, invalid reports, inconsistent counts and empty runs.

## 0.1.0 - 2026-09-11

Initial alpha release, validated on PowerBuilder 2022 R3 build 3397.

- Framework: `n_test_report`, `n_test_case`, `n_test_suite`,
  `n_test_runner`. Test discovery through `ClassDefinition`, per-test
  `setup`/`teardown`, runtime errors caught and reported with their
  location, JUnit XML output, `/out=`, `/suite=`, `/exit` switches, exit
  code equal to the failure count.
- Templates: test application, root suite, example case, icon, `.pbt`.
- Driver: `pb-test run|results|inspect|runtimes|serve`; MCP tools
  `pb_run_*` and `pb_ui_*`.
- Pre-release review: reject conflicts between requested runtimes and
  executable XML RuntimePath. Use keyboard input directly for DataWindow
  cells; escape key syntax in literal text. Expose cell rectangles and
  label visual row groups as non-logical. Reject empty or inconsistent
  passing CLI runs and stop the child before returning.
- Validation: PB 2019 R3 UI probe with the loaded runtime DLL checked;
  PB 2022 R3 passing and negative targets through CLI and MCP from an
  installed wheel in a fresh environment. PB 2025 R2 is unverified.
  See `docs/validation.md`.
