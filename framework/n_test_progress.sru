$PBExportHeader$n_test_progress.sru
$PBExportComments$pb-test: reference-type progress observer; never pass the auto-instantiated session as an observer
forward
global type n_test_progress from n_test_listener
end type
end forward

global type n_test_progress from n_test_listener
end type
global n_test_progress n_test_progress

type variables
private w_test_progress iw_progress
end variables

forward prototypes
public subroutine of_open (string as_request, string as_suite)
public subroutine of_finish (string as_title, string as_summary)
public subroutine of_progress (string as_suite, string as_case, string as_test, string as_status, string as_message, long al_time_ms, boolean ab_running, long al_completed, long al_passed, long al_failed, long al_errors, long al_case_done, long al_case_total)
public subroutine of_note (string as_message)
end prototypes

public subroutine of_open (string as_request, string as_suite);Open(iw_progress)
iw_progress.of_start(as_request, as_suite)
Yield()
end subroutine

public subroutine of_finish (string as_title, string as_summary);if IsValid(iw_progress) then iw_progress.of_finish(as_title, as_summary)
end subroutine

public subroutine of_progress (string as_suite, string as_case, string as_test, string as_status, string as_message, long al_time_ms, boolean ab_running, long al_completed, long al_passed, long al_failed, long al_errors, long al_case_done, long al_case_total);if not IsValid(iw_progress) then return
iw_progress.of_progress(as_suite, as_case, as_test, as_status, as_message, al_time_ms, ab_running, al_completed, al_passed, al_failed, al_errors, al_case_done, al_case_total)
// Cooperative message pumping, not a worker thread.
Yield()
end subroutine

public subroutine of_note (string as_message);if not IsValid(iw_progress) then return
iw_progress.of_note(as_message)
Yield()
end subroutine

on n_test_progress.create
call super::create
end on

on n_test_progress.destroy
// A completed window stays visible when its session leaves scope.
call super::destroy
end on
