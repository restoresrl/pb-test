$PBExportHeader$n_test_options.sru
$PBExportComments$pb-test: values exchanged with the interactive test setup window
forward
global type n_test_options from nonvisualobject
end type
end forward

global type n_test_options from nonvisualobject
end type
global n_test_options n_test_options

type variables
public string suite_names[]
public string suite = ""
public string output_path = ""
public boolean accepted = false
end variables

on n_test_options.create
call super::create
TriggerEvent(this, "constructor")
end on

on n_test_options.destroy
TriggerEvent(this, "destructor")
call super::destroy
end on
