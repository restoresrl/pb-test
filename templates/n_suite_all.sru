$PBExportHeader$n_suite_all.sru
$PBExportComments$pb-test: root suite. List every test case or sub-suite in ue_execute
forward
global type n_suite_all from n_test_suite
end type
end forward

global type n_suite_all from n_test_suite
end type
global n_suite_all n_suite_all

event ue_execute;// one typed variable per test case or sub-suite: that reference is what keeps the class in the executable
n_test_example lnv_example
lnv_example = create n_test_example
of_run_case(lnv_example)
end event

on n_suite_all.create
call super::create
TriggerEvent( this, "constructor" )
end on

on n_suite_all.destroy
TriggerEvent( this, "destructor" )
call super::destroy
end on
