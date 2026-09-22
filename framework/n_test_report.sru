$PBExportHeader$n_test_report.sru
$PBExportComments$pb-test: collects test outcomes and publishes JSON reports
forward
global type n_test_report from nonvisualobject
end type
end forward

global type n_test_report from nonvisualobject
end type
global n_test_report n_test_report

type prototypes
function boolean MoveFileW (string existing_name, string new_name) library "kernel32.dll"
end prototypes

type variables
private string is_suite[]
private string is_case[]
private string is_test[]
private string is_status[]
private string is_message[]
private long il_time_ms[]
private long il_count = 0
private long il_current = 0
private long il_started_ms = 0
private n_test_listener inv_listener
private long il_case_done = 0
private long il_case_total = 0
end variables

forward prototypes
public subroutine of_set_listener (n_test_listener anv_listener)
public subroutine of_begin_case (long al_total)
public subroutine of_note (string as_message)
private subroutine of_notify (boolean ab_running)
public subroutine of_begin_test (string as_suite, string as_case, string as_test)
public subroutine of_add_failure (string as_message)
public subroutine of_add_error (string as_message)
public subroutine of_end_test ()
public function long of_count ()
public function long of_count_status (string as_status)
public function string of_status (long al_index)
public function string of_json (string as_request_id, string as_application, string as_requested_suite, string as_suite, string as_runner_error)
public function integer of_publish (string as_path, string as_content)
public function integer of_write_file (string as_path, string as_content)
public function string of_summary ()
end prototypes

public subroutine of_set_listener (n_test_listener anv_listener);inv_listener = anv_listener
end subroutine

public subroutine of_begin_case (long al_total);il_case_done = 0
il_case_total = al_total
end subroutine

public subroutine of_note (string as_message);if IsNull(inv_listener) then return
if not IsValid(inv_listener) then return
inv_listener.of_note(as_message)
end subroutine

private subroutine of_notify (boolean ab_running);long ll_completed, ll_passed
if IsNull(inv_listener) then return
if not IsValid(inv_listener) then return
ll_completed = il_count
ll_passed = of_count_status("pass")
if ab_running then
	ll_completed = ll_completed - 1
	ll_passed = ll_passed - 1
end if
inv_listener.of_progress(is_suite[il_count], is_case[il_count], is_test[il_count], is_status[il_count], is_message[il_count], il_time_ms[il_count], ab_running, ll_completed, ll_passed, of_count_status("fail"), of_count_status("error"), il_case_done, il_case_total)
end subroutine

public subroutine of_begin_test (string as_suite, string as_case, string as_test);il_count = il_count + 1
il_current = il_count
is_suite[il_count] = as_suite
is_case[il_count] = as_case
is_test[il_count] = as_test
is_status[il_count] = "pass"
is_message[il_count] = ""
il_time_ms[il_count] = 0
il_started_ms = Cpu()
of_notify(true)
end subroutine

public subroutine of_add_failure (string as_message);if il_current = 0 then return
if IsNull(as_message) then as_message = "(null message)"
if is_status[il_current] = "pass" then is_status[il_current] = "fail"
if is_message[il_current] <> "" then is_message[il_current] = is_message[il_current] + "~r~n"
is_message[il_current] = is_message[il_current] + as_message
end subroutine

public subroutine of_add_error (string as_message);if il_current = 0 then return
if IsNull(as_message) then as_message = "(null message)"
is_status[il_current] = "error"
if is_message[il_current] <> "" then is_message[il_current] = is_message[il_current] + "~r~n"
is_message[il_current] = is_message[il_current] + as_message
end subroutine

public subroutine of_end_test ();if il_current = 0 then return
il_time_ms[il_current] = Cpu() - il_started_ms
il_current = 0
il_case_done = il_case_done + 1
of_notify(false)
end subroutine

public function long of_count ();return il_count
end function

public function long of_count_status (string as_status);long ll_i, ll_n = 0
for ll_i = 1 to il_count
	if is_status[ll_i] = as_status then ll_n = ll_n + 1
next
return ll_n
end function

public function string of_status (long al_index);if al_index < 1 or al_index > il_count then return ""
return is_status[al_index]
end function

public function string of_json (string as_request_id, string as_application, string as_requested_suite, string as_suite, string as_runner_error);JSONGenerator lnv_json
long ll_root, ll_cases, ll_case, ll_errors, ll_i
string ls_json
lnv_json = create JSONGenerator
try
	ll_root = lnv_json.CreateJsonObject()
	lnv_json.AddItemNumber(ll_root, "schema_version", 1)
	lnv_json.AddItemString(ll_root, "request_id", as_request_id)
	lnv_json.AddItemString(ll_root, "application", as_application)
	lnv_json.AddItemString(ll_root, "requested_suite", as_requested_suite)
	lnv_json.AddItemString(ll_root, "suite", as_suite)
	lnv_json.AddItemBoolean(ll_root, "completed", true)
	lnv_json.AddItemNumber(ll_root, "tests", il_count)
	lnv_json.AddItemNumber(ll_root, "passed", of_count_status("pass"))
	lnv_json.AddItemNumber(ll_root, "failures", of_count_status("fail"))
	lnv_json.AddItemNumber(ll_root, "errors", of_count_status("error"))
	ll_errors = lnv_json.AddItemArray(ll_root, "runner_errors")
	if as_runner_error <> "" then lnv_json.AddItemString(ll_errors, as_runner_error)
	ll_cases = lnv_json.AddItemArray(ll_root, "cases")
	for ll_i = 1 to il_count
		ll_case = lnv_json.AddItemObject(ll_cases)
		lnv_json.AddItemString(ll_case, "suite", is_suite[ll_i])
		lnv_json.AddItemString(ll_case, "classname", is_case[ll_i])
		lnv_json.AddItemString(ll_case, "name", is_test[ll_i])
		lnv_json.AddItemString(ll_case, "status", is_status[ll_i])
		lnv_json.AddItemString(ll_case, "message", is_message[ll_i])
		lnv_json.AddItemNumber(ll_case, "time", Max(0, il_time_ms[ll_i]) / 1000.0)
	next
	ls_json = lnv_json.GetJsonString()
finally
	destroy lnv_json
end try
return ls_json
end function

public function integer of_publish (string as_path, string as_content);// Same-directory, no-replace rename: readers never see a partial final report.
string ls_temp
ls_temp = as_path + ".tmp"
if FileExists(as_path) or FileExists(ls_temp) then return -1
if of_write_file(ls_temp, as_content) < 0 then return -1
if not MoveFileW(ls_temp, as_path) then return -1
return 1
end function

public function integer of_write_file (string as_path, string as_content);integer li_file
li_file = FileOpen(as_path, TextMode!, Write!, LockWrite!, Replace!, EncodingUTF8!)
if li_file < 0 then return -1
if FileWriteEx(li_file, as_content) < 0 then
	FileClose(li_file)
	return -1
end if
FileClose(li_file)
return 1
end function

public function string of_summary ();string ls_text
long ll_i
ls_text = "pb-test: " + String(il_count) + " tests, " + String(of_count_status("pass")) + " passed, " + &
	String(of_count_status("fail")) + " failed, " + String(of_count_status("error")) + " errors"
for ll_i = 1 to il_count
	if is_status[ll_i] = "pass" then continue
	ls_text = ls_text + "~r~n" + Upper(is_status[ll_i]) + " " + is_case[ll_i] + "." + is_test[ll_i] + ": " + is_message[ll_i]
next
return ls_text
end function

on n_test_report.create
call super::create
TriggerEvent( this, "constructor" )
end on

on n_test_report.destroy
TriggerEvent( this, "destructor" )
call super::destroy
end on
