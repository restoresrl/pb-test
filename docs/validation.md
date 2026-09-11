# Pre-release validation

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
