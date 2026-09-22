# AGENTS.md: pb-test

For agents editing this repository. Using pb-test on a PowerBuilder
project is described in the [README](README.md) and in
[`docs/adding-a-test-target.md`](docs/adding-a-test-target.md).

## Layout

```text
framework/   PowerScript framework sources, .sru/.srw, UTF-8 BOM, CRLF
templates/   objects a project copies: test application, root suite, example case, icon, .pbt
driver/      Python package pb-test-driver: CLI + MCP server (src layout, hatchling, uv)
docs/        how to add a test target, ORCA notes
```

The `.sru` and `.srw` files are the truth; `pbtest.pbl` is a build artefact. Never
commit a PBL.

## Rules

- **PowerScript is edited as text and compiled through ORCA.** Import
  with `pb_object_import_file` from `pb-orca-mcp` and read the
  diagnostics. A change that was not imported was not tested.
- **Keep the framework dependency order**: listener, report, case, suite,
  request, runner, options, setup window, progress window, progress observer,
  session. Import project cases/suites before the target adapter. Nothing
  references forward.
- **Auto-instantiated NVOs have value semantics.** Never pass the session
  itself as a report observer. `n_test_progress` is a separate reference-type
  observer; keep one adapter instance across detection and execution.
- **Typed references only.** Never make the framework or the templates
  instantiate a test object from a string; the linker prunes it.
- **`IsValid` after `SetNull` returns null, not false.** Guard object
  arguments with `IsNull` first, then `IsValid`, in separate `if`s.
- **The driver returns data, not screenshots.** A tool result the agent
  has to look at as an image is a failure of this design.
- Python: 3.10+, `from __future__ import annotations`, full type hints,
  `mypy --strict`, `ruff` at line length 100. Run before committing:

```pwsh
cd driver
pytest
ruff check .
ruff format --check src tests
mypy src
```

- English everywhere. No `Co-Authored-By:` trailers. Never `git commit`
  or `git push` without being asked.
