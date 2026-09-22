$PBExportHeader$n_test_listener.sru
$PBExportComments$pb-test: optional typed observer; no window or runner dependencies
forward
global type n_test_listener from nonvisualobject
end type
end forward

global type n_test_listener from nonvisualobject
end type
global n_test_listener n_test_listener

forward prototypes
public subroutine of_progress (string as_suite, string as_case, string as_test, string as_status, string as_message, long al_time_ms, boolean ab_running, long al_completed, long al_passed, long al_failed, long al_errors, long al_case_done, long al_case_total)
public subroutine of_note (string as_message)
end prototypes

public subroutine of_progress (string as_suite, string as_case, string as_test, string as_status, string as_message, long al_time_ms, boolean ab_running, long al_completed, long al_passed, long al_failed, long al_errors, long al_case_done, long al_case_total);// Override in an observer. The report borrows, but never destroys, this object.
end subroutine

public subroutine of_note (string as_message);// Optional cooperative checkpoint inside a long test.
end subroutine

on n_test_listener.create
call super::create
TriggerEvent( this, "constructor" )
end on

on n_test_listener.destroy
TriggerEvent( this, "destructor" )
call super::destroy
end on
