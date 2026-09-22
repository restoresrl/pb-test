$PBExportHeader$n_test_runner.sru
$PBExportComments$pb-test: execute a JSON request, then publish after host cleanup; never exits the process
forward
global type n_test_runner from nonvisualobject
end type
end forward

global type n_test_runner from nonvisualobject
end type
global n_test_runner n_test_runner

type variables
protected n_test_report inv_report
protected n_test_listener inv_listener
protected string is_suite = ""
protected string is_error = ""
protected string is_summary = ""
protected long il_failed = -1
protected boolean ib_finished = false
end variables

forward prototypes
public subroutine of_set_listener (n_test_listener anv_listener)
public subroutine of_host_error (string as_error)
public function long of_execute (n_test_request anv_request, n_test_suite anv_default_suite)
public function long of_finish (n_test_request anv_request, string as_cleanup_error)
public function string of_summary ()
public function long of_failed ()
end prototypes

public subroutine of_set_listener (n_test_listener anv_listener);inv_listener = anv_listener
end subroutine

public subroutine of_host_error (string as_error);if not IsValid(inv_report) then inv_report = create n_test_report
if is_error <> "" then is_error = is_error + "~r~n"
is_error = is_error + as_error
is_summary = inv_report.of_summary() + "~r~n" + is_error
if il_failed < 0 then il_failed = 0
il_failed = il_failed + 1
end subroutine

public function long of_execute (n_test_request anv_request, n_test_suite anv_default_suite);// Takes ownership of the suite. The host keeps ownership of the request.
n_test_suite lnv_suite
boolean lb_valid
if IsValid(inv_report) then destroy inv_report
inv_report = create n_test_report
inv_report.of_set_listener(inv_listener)
is_error = ""
is_summary = ""
is_suite = ""
il_failed = 0
ib_finished = false
lnv_suite = anv_default_suite
try
	if IsNull(anv_request) then
		is_error = "Null test request"
	else
		if not IsValid(anv_request) then
			is_error = "Invalid test request"
		else
			if not anv_request.requested or anv_request.error_text <> "" then
				is_error = "Request was not acquired successfully: " + anv_request.error_text
			else
				is_suite = anv_request.suite
				lb_valid = false
				if not IsNull(lnv_suite) then lb_valid = IsValid(lnv_suite)
				if not lb_valid then
					is_error = "The host supplied no valid typed suite"
				elseif is_suite <> "" and Lower(ClassName(lnv_suite)) <> is_suite then
					is_error = "The host did not select the requested suite: " + is_suite
				else
					is_suite = Lower(ClassName(lnv_suite))
					lnv_suite.of_run(inv_report)
				end if
			end if
		end if
	end if
catch (Throwable lth_error)
	is_error = "Suite execution: " + lth_error.GetMessage()
finally
	if not IsNull(lnv_suite) then
		if IsValid(lnv_suite) then destroy lnv_suite
	end if
end try
il_failed = inv_report.of_count_status("fail") + inv_report.of_count_status("error")
if inv_report.of_count() = 0 and is_error = "" then is_error = "The selected suite executed no tests"
if is_error <> "" then il_failed = il_failed + 1
is_summary = inv_report.of_summary()
if is_error <> "" then is_summary = is_summary + "~r~n" + is_error
return il_failed
end function

public function long of_finish (n_test_request anv_request, string as_cleanup_error);// Publish only after host cleanup. A failed publication leaves the active request for inspection.
string ls_json
if ib_finished then return -1
if not IsValid(inv_report) then return -1
if IsNull(anv_request) then return -1
if not IsValid(anv_request) then return -1
if anv_request.error_text <> "" or not anv_request.requested then return -1
if IsNull(as_cleanup_error) then as_cleanup_error = "Unknown cleanup error"
if as_cleanup_error <> "" then
	is_error = is_error + "~r~nHost cleanup: " + as_cleanup_error
	is_summary = is_summary + "~r~nHost cleanup: " + as_cleanup_error
	il_failed = il_failed + 1
end if
try
	ls_json = inv_report.of_json(anv_request.request_id, anv_request.application, anv_request.suite, is_suite, is_error)
	if inv_report.of_publish(anv_request.output_path, ls_json) < 0 then
		is_summary = is_summary + "~r~nCould not publish " + anv_request.output_path
		return -1
	end if
catch (Throwable lth_error)
	is_summary = is_summary + "~r~nReport publication: " + lth_error.GetMessage()
	return -1
end try
ib_finished = true
return il_failed
end function

public function string of_summary ();return is_summary
end function

public function long of_failed ();return il_failed
end function

on n_test_runner.create
call super::create
TriggerEvent( this, "constructor" )
end on

on n_test_runner.destroy
TriggerEvent( this, "destructor" )
if IsValid(inv_report) then destroy inv_report
call super::destroy
end on
