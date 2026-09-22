# Validation

## JSON workflow, released as 0.2.0 (2026-09-22)

The framework was imported through
`pb_object_import_file` into disposable PBLs on PB 2022 R3 build 3397,
x86. At the first JSON checkpoint, the five framework objects and the
host/suite/case templates compiled, followed by a full rebuild and EXE
creation.
No existing deployment was replaced.

Live EXE checks covered:

- no request: normal exit without executing tests;
- the negative template: five tests, three passed, one failure, one error,
  matching JSON and process exit 2;
- a green exported fixture with negative demo events renamed out of
  discovery: three tests passed with exit 0;
- a different suite selected by name through typed host branches, with
  the test library deployed as a PBD;
- Unicode paths, relative output paths, input with/without UTF-8 BOM,
  and native JSON message roundtrips with quotes, slash, tabs, newlines
  and Unicode;
- missing suite reported as a runner error rather than a green run;
- malformed JSON, expiry, wrong application, wrong field type, unknown
  field, unsupported schema and duplicate keys rejected before tests;
- another launch while the request was active: rejected without rerun.

The driver wheel was built from its sdist and installed in a fresh Python
3.12 x64 environment. CLI execution and a real MCP stdio client ran the
PBD-selected green suite. The client discovered all 16 tools, prepared
and launched a run, checked exit/results, then reconnected to a new server
to read and release the persisted request receipt. This verifies that
report collection does not depend on an in-memory process handle.

Automated driver tests cover JSON validation, no-clobber publication,
slot ownership, pending cancellation, expiry, timeout without process
control, Unicode, stale/mismatched reports, CLI exits and MCP transport.
The pb-ai-code checks cover setup/use skill delivery, installed links,
IDE handoffs and baseline/final evidence instructions. At this checkpoint,
73 driver tests and 296 pb-ai-code tests passed, along with ruff, format
checks and strict mypy in both repositories.

A user subsequently ran the prepared target from the IDE. Its matching
request ID, application and suite produced three passing tests in JSON.
The user retried because there was no visible completion feedback; the
retained rejection diagnostic reported an existing output, and the valid
report remained readable. No IDE process exit was observed by the driver.

A completion-only notice was subsequently compiled and checked as an
EXE, along with empty-suite, cleanup-error and failed-publication summaries.
That notice has been replaced by the session/progress implementation below.

### Auto-instantiated service and progress window

All nine framework sources, including the window and separate reference-type
observer, were imported through ORCA on the same PB 2022 R3 x86 runtime.
The target adapter and simplified Application compiled, rebuilt and linked.
Live checks covered:

- ordinary startup without a request, with exit 0;
- the unchanged negative example: five tests, three passed, one failure,
  one error and exit 2, without an EXE progress window;
- repeated launch, malformed JSON and missing suite, without a green result;
- adapter cleanup returning an error or raising an exception, suite selection
  raising an exception, and a publication collision. Errors were retained,
  no uncaught runtime dialog appeared, and the collision preserved its file;
- an explicitly visible EXE with three delayed tests and cooperative
  checkpoints. Win32 observations captured each running test caption;
  post-run UI data contained three completed/passed tests and PASSED;
- rejection of an early window-close request, repeated `of_run()` and
  reentrant calls on both the same and a different adapter instance;
- execution from a helper function with a local auto-instantiated adapter.
  Its completed window remained open after the local left scope. Closing
  it through the driver produced exit 0 with no runtime error;
- the same delayed green fixture with the canonical host and default EXE
  settings: three passes, about 15 seconds, exit 0 and no progress window.

The UI probe exposed PowerBuilder's auto-instantiated object copy semantics;
progress uses a separate reference-type observer rather than passing the
session itself. It also exposed a click-result read after the clicked
control had closed its process. The driver now captures that metadata
before clicking, with regression tests for invoke and mouse methods.

At this checkpoint, 75 driver tests and 297 pb-ai-code tests passed.
Ruff, format checks and strict mypy passed in both repositories.
The progress checks read native window/control data from an EXE; they do
not prove the user's IDE rendering or a responsive blocking SQL call.
The user then confirmed the progress window in the IDE.

The next revision added the inline per-test summary and interactive setup.
All eleven framework objects and the updated adapter compiled through ORCA,
followed by a full rebuild and EXE creation. A user-started EXE probe, with
no pre-created request, selected the registered suite in the setup window
and pressed Start. The progress window retained five ordered rows: three
PASS, one FAIL with both assertion messages, and one ERROR with its runtime
message and duration. Counts and the NOT PASSED title matched the JSON.
The internally created request/active files were removed, the report was
retained, and closing the result produced exit 2 without a runtime dialog.
A separate Cancel probe exited 0 and created no control or report files.
A delayed interactive fixture then displayed three PASS rows of about 5.4
seconds each and exited 0. The standard driver-prepared negative run still
produced the same five results and exit 2 without an EXE window.

JSON framework compatibility with PB 2019/2025, real legacy application
initialization/cleanup, database integration, remote filesystems and x64
PowerBuilder builds remain unverified. The historical UI checks below
are not new JSON-framework evidence.

## Historical v0.1.0 pre-release validation

This records the local checks completed on 2026-09-11 before the
0.1.0 alpha release. Preview artifacts mentioned below were built
before versioning and publication; they are not release assets.

## PowerBuilder coverage

| Environment | Verified | Not verified |
| --- | --- | --- |
| PB 2022 R3 build 3397, x86 | Framework/templates imported into fresh PBLs through ORCA; passing and negative executables run through CLI and MCP | Database integration and other application architectures |
| PB 2019 R3 build 2803, x86 | Grid/freeform field reads, row insertion, keyboard cell edits, runtime-error capture | The PowerScript test framework on this release |
| PB 2025 R2 build 6430 | No runtime result | ORCA DLL loading failed with WinError 182; cause unresolved |

The first reported 2019 result was wrong: the script launched the 2022
sample. Fixing the executable path was not enough, because the 2019
executable's XML still selected the 2022 runtime. The successful repeat
checked the process image and the loaded `PBVM.dll` path after correcting
RuntimePath in the disposable test deployment.

Freeform cells were readable, but grouping them by rectangle top split
one record into three visual groups. These groups are not logical rows.
A grid's active editor can also appear as an extra cell. The API keeps
the raw observations and marks `rows_are_logical=false`; callers must
not use visual groups as a DataWindow record count.

## Framework and installed driver

The current framework and templates were imported through ORCA into
new libraries. The original example produced five tests: three passed,
one failed with two assertion messages, and one raised a caught runtime
error. The process and CLI both returned 2.

For a green run, the example was exported through ORCA, its two negative
events renamed out of `test_*` discovery, reimported and rebuilt at a
separate path. That executable ran three tests, all passed, with exit 0.
The negative sample remains unchanged in `templates/`.

`uv build` built the driver wheel from its source distribution. The
wheel was installed into a fresh Python 3.12 x64 environment; imports
resolved to `site-packages`, not the working checkout. Both executables
then passed their expected checks through:

- the installed CLI, checking actual subprocess exit codes;
- a real MCP stdio client, including initialization, discovery of all
  12 tools, start/wait/results calls and process cleanup.

The installed MCP server also read the 2019 sample, typed literal
`a+b^{x}%` into a grid cell, reread the value and captured/dismissed the
intentional `R0002` dialog. An earlier attempt found that ValuePattern
could partially change the cell before keyboard fallback duplicated
the text. The driver now uses keyboard input directly for DataWindow
cells; the repeated check passed.

## Automated checks and packaging

| Repository | Tests | Other checks |
| --- | --- | --- |
| pb-test driver | 32 passed | ruff, format check, strict mypy |
| pb-orca-mcp local patch | 254 passed, including 25 PB-dependent tests | ruff, format check, strict mypy |
| pb-ai-code integration | 275 passed | ruff, format check, mypy |

The driver tests include a real stdio server handshake, JUnit tool calls,
runtime-selection conflicts, literal-key escaping and CLI exit handling.
PB-dependent ORCA tests used x86 Python with `PB_ORCA_MCP_HAS_PB=1`.

Wheel inspection checked licence files and the ORCA default icon. The
Python wheel deliberately excludes PowerScript sources; a source-preview
ZIP contains the framework, templates, driver sources/tests and guides.
These are local preview artifacts, not release assets. The ORCA preview
still carries version `0.2.8` and must not be published under that
existing release number.

## Build-output protection

The reviewed ORCA patch rejects an existing EXE before calling ORCA.
The live test compared the working executable's SHA-256 before and
after both a rejected rebuild and a failed build at another destination.
It remained unchanged. The agent must build to a new location and check
the response and runtime XML before replacing any deployment explicitly.

The patch supplies a default icon and one 0/1 selection per library.
Legacy flag lists accept only masks 0 and 1. It does not guarantee
atomic deployment or cleanup of partial output after a failed build.

## Release checks

The release workflow checks CI before tagging pb-test v0.1.0 and
pb-orca-mcp v0.2.9. pb-ai-code then pins both tags and tests the
installer and server configuration. This local test report does not
replace those release checks.

PB 2025 loading, other DataWindow styles, off-screen cells, MDI and
database test patterns remain outside this validation. UI operations
need an interactive desktop and callers must reread values after edits.
