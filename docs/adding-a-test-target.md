# Adding a test target to an existing workspace

A separate target is optional. For complex applications that need their
own initialization, prefer [integrating tests](integrating-tests.md) into
the existing target. Both layouts use the same JSON request protocol.

The pattern is a second target in the same workspace: `test_<app>.pbt`,
whose library list is the application's list plus `test_<app>.pbl` and
`pbtest.pbl`. The test application object lives in `test_<app>.pbl`
and only ever runs the suites. Test cases go into one `test_<lib>.pbl`
per application PBL, or all into `test_<app>.pbl` for a small project.

## With the IDE

1. New target, Application, name `test_<app>`, library `test_<app>.pbl`.
2. Library list: add every PBL of the application and `pbtest.pbl`.
3. Import the framework in the order shown in the
   [integration guide](integrating-tests.md).
4. Import `templates/n_test_example.sru`, `templates/n_suite_all.sru`,
   `templates/n_test_app.sru`, then `templates/test_myapp.sra` into the
   test library. Rename the Application object and its `appname` to
   `test_<app>`. The auto-instantiated adapter handles execution and UI.
5. Prepare `<application>_test.json` in the actual IDE startup directory
   with `pb-test prepare`, then run the target. Without a request, the
   template does not execute tests. Read the matching JSON report using
   the returned receipt; see [JSON protocol](json-protocol.md).

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
pb_object_import_file(framework/n_test_listener.sru, pbtest.pbl)
pb_object_import_file(framework/n_test_report.sru, pbtest.pbl)
pb_object_import_file(framework/n_test_case.sru,   pbtest.pbl)
pb_object_import_file(framework/n_test_suite.sru,  pbtest.pbl)
pb_object_import_file(framework/n_test_request.sru, pbtest.pbl)
pb_object_import_file(framework/n_test_runner.sru, pbtest.pbl)
pb_object_import_file(framework/n_test_options.sru, pbtest.pbl)
pb_object_import_file(framework/w_test_setup.srw, pbtest.pbl)
pb_object_import_file(framework/w_test_progress.srw, pbtest.pbl)
pb_object_import_file(framework/n_test_progress.sru, pbtest.pbl)
pb_object_import_file(framework/n_test_session.sru, pbtest.pbl)
pb_object_import_file(n_test_example.sru, test_<app>.pbl)
pb_object_import_file(n_suite_all.sru, test_<app>.pbl)
pb_object_import_file(n_test_app.sru, test_<app>.pbl)
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
pb-test run C:\proj\test_<app>.exe --application test_<app> --runtime-version 22.2 --out C:\results\run-001\result.json
```

From an agent session, call `pb_test_prepare`, then `pb_run_start` with
the same working directory and no test switches. Combine `pb_run_wait`
with `pb_test_status` for the receipt, then release completed control
files with `pb_test_cleanup`. For IDE execution, prepare the request and
ask the user to Run; no EXE creation or driver launch is required. A
project can also expose the adapter's `of_interactive()` method from a
menu or button for user-started runs without an agent.

## Deployment note

The executable contains only the objects reachable from the application
object through typed references. That is why suites hold a typed
variable per test case. For alternative suite names, add explicit typed
selection branches in the adapter's `of_suite()` method. The runner
validates the selected class against the request and never uses
`create using`. The sample registers only `n_suite_all`.

If distributing test libraries as PBDs, build them with
`pb_dynamic_library_create` before EXE creation and deploy them beside
the EXE. With pb-orca-mcp v0.2.9, set that library's `pbd` entry to `true`.
The v0.2.8 spelling is `["machine_code"]`, which encodes the integer 1;
that entry selects a prebuilt library and does not compile it. `"pbd"`
is not a valid flag name.
