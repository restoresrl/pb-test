# Adding a test target to an existing workspace

The pattern is a second target in the same workspace: `test_<app>.pbt`,
whose library list is the application's list plus `test_<app>.pbl` and
`pbtest.pbl`. The test application object lives in `test_<app>.pbl`
and only ever runs the suites. Test cases go into one `test_<lib>.pbl`
per application PBL, or all into `test_<app>.pbl` for a small project.

## With the IDE

1. New target, Application, name `test_<app>`, library `test_<app>.pbl`.
2. Library list: add every PBL of the application and `pbtest.pbl`.
3. Import `templates/test_myapp.sra` into `test_<app>.pbl`, rename the
   object and its `appname` to `test_<app>`.
4. Import `templates/n_suite_all.sru` and `templates/n_test_example.sru`.
5. Run the target. A message box shows the summary; the JUnit XML is
   written next to the current directory as `test_<app>.test.result.xml`.

## With ORCA (`pb-orca-mcp`)

ORCA has two rules that shape the order of operations:

- the library list and the current application are set **once per
  session**. Changing either means closing and reopening the session;
- an object cannot be imported until a current application is set, and
  the current application must already exist in its PBL. A brand-new
  application object therefore has to be imported with **another**
  application as the current one.

So, to create the target from scratch:

```text
pb_session_open(pb_version)
pb_library_create(test_<app>.pbl)
pb_library_create(pbtest.pbl)                    # once per machine or project
pb_set_library_list([test_<app>.pbl, pbtest.pbl, <app>.pbl, ...])
pb_set_current_application(<app>.pbl, <app>)     # the real application, as bootstrap
pb_object_import_file(framework/n_test_report.sru, pbtest.pbl)
pb_object_import_file(framework/n_test_case.sru,   pbtest.pbl)
pb_object_import_file(framework/n_test_suite.sru,  pbtest.pbl)
pb_object_import_file(framework/n_test_runner.sru, pbtest.pbl)
pb_object_import_file(n_test_*.sru, test_<app>.pbl)
pb_object_import_file(n_suite_all.sru, test_<app>.pbl)
pb_object_import_file(test_<app>.sra, test_<app>.pbl)
pb_session_close()
pb_session_open(pb_version)
pb_set_library_list([test_<app>.pbl, pbtest.pbl, <app>.pbl, ...])
pb_set_current_application(test_<app>.pbl, test_<app>)
pb_application_rebuild("full")
pb_executable_create(<new-build-dir>/test_<app>.exe)
```

The framework files import in that order because each one references
the previous. Once `pbtest.pbl` exists, later sessions skip its creation
and the bootstrap dance: the test application is the current one from
the start.

On `pb-orca-mcp` v0.2.8, pass `icon_name` pointing to
`templates/pbtest.ico` and `pbd_flags=[[], [], ...]`, one empty list per
library. Missing arguments returned `PBORCA_INVALIDPARMS` in the probe.
Version 0.2.9 supplies defaults and adds `pbd`, one boolean per
library. Check the installed tool schema if the version is unknown.

Build in a new directory with the intended executable name. An existing
output caused a link error in the original probe; v0.2.9 rejects
it without changing it. Check the build response and the generated
`<exe>.xml` RuntimePath before running. Replace the previous deployment
only after success, with explicit approval. A failed build may leave a
partial output in the new directory.

The `.pbt` file is text. ORCA does not write it; the IDE does, or you
do, from `templates/test_myapp.pbt`. It is needed to open the target in
the IDE, not to build or run it through ORCA.

## Running it

```powershell
pb-test run C:\proj\test_<app>.exe --runtime-version 22.2
```

or, from an agent session, `pb_run_start` with
`args='/out=C:\proj\test_<app>.result.xml /exit'`, then `pb_run_wait`
and `pb_run_results`.

## Deployment note

The executable contains only the objects reachable from the application
object through typed references. That is why suites hold a typed
variable per test case. `/suite=<class>` on the command line uses
`create using` and so only works when the class is in a PBD (deploy
`test_<app>.pbl` as a PBD after building it with
`pb_dynamic_library_create`) or otherwise retained by the linker.
With pb-orca-mcp v0.2.9, set that library's `pbd` entry to `true`.
The v0.2.8 spelling is `["machine_code"]`, which encodes the integer 1;
that entry selects a prebuilt library and does not compile it. `"pbd"`
is not a valid flag name.
