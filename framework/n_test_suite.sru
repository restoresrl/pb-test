$PBExportHeader$n_test_suite.sru
$PBExportComments$pb-test: base class for suites. Inherit and call of_run_case / of_run_suite from ue_execute
forward
global type n_test_suite from nonvisualobject
end type
end forward

global type n_test_suite from nonvisualobject
event ue_execute ( )
end type
global n_test_suite n_test_suite

type variables
protected n_test_report inv_report
protected string is_name
protected long il_failed = 0
end variables

forward prototypes
public function long of_run (n_test_report anv_report)
public subroutine of_run_case (n_test_case anv_case)
public subroutine of_run_suite (n_test_suite anv_suite)
end prototypes

public function long of_run (n_test_report anv_report);inv_report = anv_report
is_name = Lower(ClassName(this))
il_failed = 0
this.event ue_execute()
return il_failed
end function

public subroutine of_run_case (n_test_case anv_case);// pass a fresh instance held in a typed variable. The suite destroys it.
// a typed create is what keeps the test case in the executable; a class named only by string gets pruned
boolean lb_ok = true
if IsNull(anv_case) then lb_ok = false
if lb_ok then
	if not IsValid(anv_case) then lb_ok = false
end if
if not lb_ok then
	inv_report.of_begin_test(is_name, "(suite)", "(create)")
	inv_report.of_add_error("of_run_case received a null or invalid test case")
	inv_report.of_end_test()
	il_failed = il_failed + 1
	return
end if
il_failed = il_failed + anv_case.of_run(inv_report, is_name)
destroy anv_case
end subroutine

public subroutine of_run_suite (n_test_suite anv_suite);// pass a fresh instance held in a typed variable. This suite destroys it.
boolean lb_ok = true
if IsNull(anv_suite) then lb_ok = false
if lb_ok then
	if not IsValid(anv_suite) then lb_ok = false
end if
if not lb_ok then
	inv_report.of_begin_test(is_name, "(suite)", "(create)")
	inv_report.of_add_error("of_run_suite received a null or invalid suite")
	inv_report.of_end_test()
	il_failed = il_failed + 1
	return
end if
il_failed = il_failed + anv_suite.of_run(inv_report)
destroy anv_suite
end subroutine

on n_test_suite.create
call super::create
TriggerEvent( this, "constructor" )
end on

on n_test_suite.destroy
TriggerEvent( this, "destructor" )
call super::destroy
end on
