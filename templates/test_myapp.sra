$PBExportHeader$test_myapp.sra
$PBExportComments$pb-test: test application. Rename to test_<yourapp> and keep appname in sync
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

event open;n_test_runner lnv_runner
n_suite_all lnv_suite
lnv_runner = create n_test_runner
lnv_suite = create n_suite_all
lnv_runner.of_run_from_commandline(lnv_suite)
destroy lnv_runner
end event

