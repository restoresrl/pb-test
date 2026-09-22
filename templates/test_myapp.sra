$PBExportHeader$test_myapp.sra
$PBExportComments$pb-test: demo host. Rename object/appname; the test adapter handles execution and feedback
forward
global type test_myapp from application
end type
global transaction sqlca
global dynamicdescriptionarea sqlda
global dynamicstagingarea sqlsa
global error error
global message message
end forward

global type test_myapp from application
string appname = "test_myapp"
end type
global test_myapp test_myapp

type prototypes
subroutine ExitProcess (ulong exit_code) library "kernel32.dll"
end prototypes

type variables
n_test_app inv_tests
end variables

on test_myapp.create
appname = "test_myapp"
message = create message
sqlca = create transaction
sqlda = create dynamicdescriptionarea
sqlsa = create dynamicstagingarea
error = create error
end on

on test_myapp.destroy
destroy( sqlca )
destroy( sqlda )
destroy( sqlsa )
destroy( error )
destroy( message )
end on

event open;if inv_tests.of_requested() then
	// Optional target initialization in the approved test environment.
	inv_tests.of_run()
	return
end if
// Normal application startup belongs here. This demo has no ordinary UI.
// A real menu/button can create a fresh local n_test_app, call of_interactive(),
// perform any required test initialization, then call of_run().
end event

event close;// Optional EXE host policy, not part of the test service. Never exits the IDE.
// Required test cleanup belongs in the adapter's of_cleanup, before JSON publication.
if inv_tests.of_finished() and Handle(GetApplication()) <> 0 then ExitProcess(inv_tests.of_result())
end event
