# Changelog

## Unreleased

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
