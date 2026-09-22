$PBExportHeader$w_test_progress.srw
$PBExportComments$pb-test: nonmodal progress and inline test results; never owns the host application
forward
global type w_test_progress from window
end type
type st_phase from statictext within w_test_progress
end type
type st_current from statictext within w_test_progress
end type
type st_counts from statictext within w_test_progress
end type
type st_case from statictext within w_test_progress
end type
type hpb_case from hprogressbar within w_test_progress
end type
type st_results from statictext within w_test_progress
end type
type mle_results from multilineedit within w_test_progress
end type
type st_details from statictext within w_test_progress
end type
type mle_details from multilineedit within w_test_progress
end type
type cb_close from commandbutton within w_test_progress
end type
end forward

global type w_test_progress from window
integer width = 3200
integer height = 2400
boolean titlebar = true
string title = "pb-test: running"
boolean controlmenu = true
boolean center = true
boolean resizable = true
windowtype windowtype = main!
long backcolor = 79416533
st_phase st_phase
st_current st_current
st_counts st_counts
st_case st_case
hpb_case hpb_case
st_results st_results
mle_results mle_results
st_details st_details
mle_details mle_details
cb_close cb_close
end type
global w_test_progress w_test_progress

type variables
private boolean ib_running = true
private long il_started
private string is_suite = ""
end variables

forward prototypes
public subroutine of_start (string as_request, string as_suite)
public subroutine of_progress (string as_suite, string as_case, string as_test, string as_status, string as_message, long al_time_ms, boolean ab_running, long al_completed, long al_passed, long al_failed, long al_errors, long al_case_done, long al_case_total)
public subroutine of_note (string as_message)
public subroutine of_finish (string as_title, string as_summary)
end prototypes

public subroutine of_start (string as_request, string as_suite);il_started = Cpu()
ib_running = true
cb_close.Enabled = false
st_phase.Text = "Starting tests"
is_suite = as_suite
st_current.Text = "Suite: " + as_suite
mle_results.Text = ""
mle_details.Text = "Request: " + as_request + "~r~nThe window updates at test boundaries and cooperative checkpoints. A blocking test can delay repainting."
end subroutine

public subroutine of_progress (string as_suite, string as_case, string as_test, string as_status, string as_message, long al_time_ms, boolean ab_running, long al_completed, long al_passed, long al_failed, long al_errors, long al_case_done, long al_case_total);string ls_line, ls_label
if ab_running then
	this.Title = "pb-test: running - " + as_case + "." + as_test
	st_phase.Text = "Running: " + as_case + "." + as_test
	mle_details.Text = "Running " + as_case + "." + as_test
else
	choose case as_status
		case "pass"
			ls_label = "PASS "
		case "fail"
			ls_label = "FAIL "
		case "error"
			ls_label = "ERROR"
		case else
			ls_label = Upper(as_status)
	end choose
	st_phase.Text = "Completed: " + as_case + "." + as_test + " - " + ls_label
	ls_line = "[" + ls_label + "] " + as_case + "." + as_test + "  " + String(Double(al_time_ms) / 1000, "0.000") + " s"
	if mle_results.Text <> "" then mle_results.Text = mle_results.Text + "~r~n"
	mle_results.Text = mle_results.Text + ls_line
	if as_message <> "" then
		mle_results.Text = mle_results.Text + "~r~n    " + as_message
		mle_details.Text = as_message
	else
		mle_details.Text = ls_line
	end if
end if
is_suite = as_suite
st_current.Text = "Suite: " + as_suite + "    Elapsed: " + String(Long(Max(0, Cpu() - il_started) / 1000)) + " s"
st_counts.Text = "Completed: " + String(al_completed) + "    Passed: " + String(al_passed) + "    Failed: " + String(al_failed) + "    Errors: " + String(al_errors)
st_case.Text = "Current case: " + String(al_case_done) + " / " + String(al_case_total) + " tests completed"
if al_case_total > 0 then hpb_case.Position = Long(al_case_done * 100.0 / al_case_total)
end subroutine

public subroutine of_note (string as_message);mle_details.Text = as_message
st_current.Text = "Suite: " + is_suite + "    Elapsed: " + String(Long(Max(0, Cpu() - il_started) / 1000)) + " s"
end subroutine

public subroutine of_finish (string as_title, string as_summary);this.Title = "pb-test: " + as_title
st_phase.Text = as_title
mle_details.Text = as_summary + "~r~n~r~nTests have finished. Close this window before starting another run."
ib_running = false
cb_close.Enabled = true
end subroutine

on w_test_progress.create
this.st_phase = create st_phase
this.st_current = create st_current
this.st_counts = create st_counts
this.st_case = create st_case
this.hpb_case = create hpb_case
this.st_results = create st_results
this.mle_results = create mle_results
this.st_details = create st_details
this.mle_details = create mle_details
this.cb_close = create cb_close
this.Control[] = {this.st_phase, this.st_current, this.st_counts, this.st_case, this.hpb_case, this.st_results, this.mle_results, this.st_details, this.mle_details, this.cb_close}
end on

on w_test_progress.destroy
destroy(this.st_phase)
destroy(this.st_current)
destroy(this.st_counts)
destroy(this.st_case)
destroy(this.hpb_case)
destroy(this.st_results)
destroy(this.mle_results)
destroy(this.st_details)
destroy(this.mle_details)
destroy(this.cb_close)
end on

event closequery;// No forced cancellation while fixtures may still own application resources.
if ib_running then return 1
return 0
end event

type st_phase from statictext within w_test_progress
integer x = 64
integer y = 40
integer width = 3030
integer height = 120
integer textsize = -11
integer weight = 700
string facename = "Segoe UI"
long backcolor = 79416533
string text = "Starting tests"
end type

type st_current from statictext within w_test_progress
integer x = 64
integer y = 180
integer width = 3030
integer height = 90
integer textsize = -9
string facename = "Segoe UI"
long backcolor = 79416533
string text = "Suite"
end type

type st_counts from statictext within w_test_progress
integer x = 64
integer y = 290
integer width = 3030
integer height = 90
integer textsize = -9
string facename = "Segoe UI"
long backcolor = 79416533
string text = "Completed: 0    Passed: 0    Failed: 0    Errors: 0"
end type

type st_case from statictext within w_test_progress
integer x = 64
integer y = 400
integer width = 3030
integer height = 90
integer textsize = -9
string facename = "Segoe UI"
long backcolor = 79416533
string text = "Current case: discovering tests"
end type

type hpb_case from hprogressbar within w_test_progress
integer x = 64
integer y = 500
integer width = 3030
integer height = 90
unsignedinteger minposition = 0
unsignedinteger maxposition = 100
end type

type st_results from statictext within w_test_progress
integer x = 64
integer y = 625
integer width = 3030
integer height = 80
integer textsize = -9
integer weight = 700
string facename = "Segoe UI"
long backcolor = 79416533
string text = "Test results"
end type

type mle_results from multilineedit within w_test_progress
integer x = 64
integer y = 715
integer width = 3030
integer height = 900
integer textsize = -9
string facename = "Consolas"
boolean displayonly = true
boolean vscrollbar = true
string text = ""
end type

type st_details from statictext within w_test_progress
integer x = 64
integer y = 1645
integer width = 3030
integer height = 80
integer textsize = -9
integer weight = 700
string facename = "Segoe UI"
long backcolor = 79416533
string text = "Current message / final summary"
end type

type mle_details from multilineedit within w_test_progress
integer x = 64
integer y = 1735
integer width = 3030
integer height = 340
integer textsize = -9
string facename = "Segoe UI"
boolean displayonly = true
boolean vscrollbar = true
string text = ""
end type

type cb_close from commandbutton within w_test_progress
integer x = 2630
integer y = 2120
integer width = 460
integer height = 120
integer textsize = -9
string facename = "Segoe UI"
string text = "Close"
boolean enabled = false
end type

event clicked;Close(Parent)
end event
