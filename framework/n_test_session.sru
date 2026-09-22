$PBExportHeader$n_test_session.sru
$PBExportComments$pb-test: auto-instantiated entry point; check once, initialize the host, then run
forward
global type n_test_session from nonvisualobject
end type
end forward

shared variables
boolean sb_running = false
end variables

global type n_test_session from nonvisualobject autoinstantiate
end type

type variables
private n_test_request inv_request
private n_test_progress inv_progress
private boolean ib_checked = false
private boolean ib_running = false
private boolean ib_finished = false
private boolean ib_ui_override = false
private boolean ib_show_ui = false
private integer ii_request = 0
private long il_result = -1
private string is_summary = ""
end variables

forward prototypes
public function boolean of_requested ()
public function boolean of_interactive ()
public function long of_run ()
public function n_test_suite of_suite (string as_name)
public subroutine of_suite_names (ref string as_names[])
public function string of_cleanup ()
public function string of_requested_suite ()
public function string of_error ()
public function string of_summary ()
public function long of_result ()
public function boolean of_finished ()
public subroutine of_show_progress (boolean ab_show)
public subroutine of_note (string as_message)
end prototypes

public function boolean of_requested ();// True also on rejection: never fall through into normal startup with a bad request.
if not ib_checked then
	ib_checked = true
	inv_request = create n_test_request
	if sb_running then
		ii_request = -1
		inv_request.error_text = "Another test session is already running in this process"
	else
		ii_request = inv_request.of_acquire()
	end if
end if
return ii_request <> 0
end function

public function boolean of_interactive ();// Configure a user-started request. The host still decides initialization and calls of_run.
n_test_options lnv_options
w_test_setup lw_setup
string ls_names[]
boolean lb_accepted
if ib_running or ib_finished or sb_running then return false
if of_requested() then return true
lnv_options = create n_test_options
try
	this.of_suite_names(ls_names)
	if UpperBound(ls_names) = 0 then
		MessageBox("pb-test", "This target has no suites registered for interactive execution.", Exclamation!)
		return false
	end if
	lnv_options.suite_names = ls_names
	lnv_options.output_path = inv_request.of_default_output()
	OpenWithParm(lw_setup, lnv_options)
	lb_accepted = lnv_options.accepted
	if not lb_accepted then return false
	ii_request = inv_request.of_prepare_interactive(lnv_options.suite, lnv_options.output_path)
	ib_ui_override = true
	ib_show_ui = true
catch (Throwable lth_setup)
	inv_request.requested = true
	inv_request.error_text = "Interactive test setup: " + lth_setup.GetMessage()
	ii_request = -1
	ib_ui_override = true
	ib_show_ui = true
	lb_accepted = true
finally
	destroy lnv_options
end try
return lb_accepted
end function

public function long of_run ();// Synchronous. No HALT, ExitProcess or host-window changes. The host owns its lifecycle.
n_test_runner lnv_runner
n_test_suite lnv_suite
string ls_cleanup, ls_select_error, ls_title, ls_detail, ls_suite
boolean lb_published = false
if ib_running or ib_finished or sb_running then return -1
if not of_requested() then return -1
ib_running = true
sb_running = true
il_result = 3
SetNull(lnv_suite)
lnv_runner = create n_test_runner
try
	if not ib_ui_override then ib_show_ui = Handle(GetApplication()) = 0
	if ib_show_ui then
		inv_progress = create n_test_progress
		ls_suite = inv_request.suite
		if ls_suite = "" then ls_suite = "(target default)"
		inv_progress.of_open(inv_request.request_id, ls_suite)
	end if
	if ii_request < 0 then
		is_summary = "Request rejected: " + inv_request.error_text
	else
		if IsValid(inv_progress) then lnv_runner.of_set_listener(inv_progress)
		try
			lnv_suite = this.of_suite(inv_request.suite)
		catch (Throwable lth_select)
			ls_select_error = "Suite selection: " + lth_select.GetMessage()
		end try
		lnv_runner.of_execute(inv_request, lnv_suite)
		if ls_select_error <> "" then lnv_runner.of_host_error(ls_select_error)
	end if
catch (Throwable lth_run)
	lnv_runner.of_host_error("Test session: " + lth_run.GetMessage())
	is_summary = lnv_runner.of_summary()
finally
	// The adapter's cleanup is inside the result boundary, including rejected requests.
	try
		ls_cleanup = this.of_cleanup()
	catch (Throwable lth_cleanup)
		ls_cleanup = lth_cleanup.GetMessage()
	end try
	if ii_request > 0 then
		il_result = lnv_runner.of_finish(inv_request, ls_cleanup)
		lb_published = il_result >= 0
		is_summary = lnv_runner.of_summary()
		if il_result < 0 then il_result = 3
	else
		if not IsNull(ls_cleanup) then
			if ls_cleanup <> "" then is_summary = is_summary + "~r~nHost cleanup: " + ls_cleanup
		end if
	end if
	destroy lnv_runner
	ib_running = false
	ib_finished = true
	sb_running = false
end try
if ib_show_ui then
	if IsValid(inv_progress) then
		choose case true
			case ii_request < 0
				ls_title = "Request rejected"
			case not lb_published
				ls_title = "Report not saved"
			case il_result = 0
				ls_title = "PASSED"
			case else
				ls_title = "NOT PASSED"
		end choose
		ls_detail = is_summary + "~r~nRequest: " + inv_request.request_id
		if lb_published then
			ls_detail = ls_detail + "~r~nReport: " + inv_request.output_path
		else
			ls_detail = ls_detail + "~r~nNo completed report was published."
		end if
		inv_progress.of_finish(ls_title, ls_detail)
	end if
end if
inv_request.of_release_interactive()
return il_result
end function

public function n_test_suite of_suite (string as_name);// Override in a target adapter. Create suites through typed references only.
n_test_suite lnv_none
SetNull(lnv_none)
return lnv_none
end function

public subroutine of_suite_names (ref string as_names[]);// Override with every suite exposed by the interactive setup window.
string ls_empty[]
as_names = ls_empty
end subroutine

public function string of_cleanup ();// Override for target-specific cleanup that must precede result publication.
return ""
end function

public function string of_requested_suite ();if not ib_checked then return ""
return inv_request.suite
end function

public function string of_error ();if not ib_checked then return ""
return inv_request.error_text
end function

public function string of_summary ();return is_summary
end function

public function long of_result ();return il_result
end function

public function boolean of_finished ();return ib_finished
end function

public subroutine of_show_progress (boolean ab_show);// Optional override for interactive EXEs or private UI validation. Default: IDE only.
if ib_running or ib_finished then return
ib_ui_override = true
ib_show_ui = ab_show
end subroutine

public subroutine of_note (string as_message);if IsValid(inv_progress) then inv_progress.of_note(as_message)
end subroutine

on n_test_session.create
call super::create
TriggerEvent(this, "constructor")
end on

on n_test_session.destroy
TriggerEvent(this, "destructor")
if IsValid(inv_progress) then destroy inv_progress
if IsValid(inv_request) then destroy inv_request
// Open windows belong to PowerBuilder, not to this scoped NVO. A completed
// progress window stays visible even when a local auto-instantiated helper leaves scope.
call super::destroy
end on
