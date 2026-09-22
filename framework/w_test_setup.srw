$PBExportHeader$w_test_setup.srw
$PBExportComments$pb-test: interactive setup for a user-started JSON test request
forward
global type w_test_setup from window
end type
type st_intro from statictext within w_test_setup
end type
type st_suite from statictext within w_test_setup
end type
type ddlb_suite from dropdownlistbox within w_test_setup
end type
type st_output from statictext within w_test_setup
end type
type sle_output from singlelineedit within w_test_setup
end type
type st_note from statictext within w_test_setup
end type
type cb_start from commandbutton within w_test_setup
end type
type cb_cancel from commandbutton within w_test_setup
end type
end forward

global type w_test_setup from window
integer width = 3000
integer height = 1250
boolean titlebar = true
string title = "pb-test: configure tests"
boolean controlmenu = true
boolean center = true
windowtype windowtype = response!
long backcolor = 79416533
st_intro st_intro
st_suite st_suite
ddlb_suite ddlb_suite
st_output st_output
sle_output sle_output
st_note st_note
cb_start cb_start
cb_cancel cb_cancel
end type
global w_test_setup w_test_setup

type variables
private n_test_options inv_options
end variables

on w_test_setup.create
this.st_intro = create st_intro
this.st_suite = create st_suite
this.ddlb_suite = create ddlb_suite
this.st_output = create st_output
this.sle_output = create sle_output
this.st_note = create st_note
this.cb_start = create cb_start
this.cb_cancel = create cb_cancel
this.Control[] = {this.st_intro, this.st_suite, this.ddlb_suite, this.st_output, this.sle_output, this.st_note, this.cb_start, this.cb_cancel}
end on

on w_test_setup.destroy
destroy(this.st_intro)
destroy(this.st_suite)
destroy(this.ddlb_suite)
destroy(this.st_output)
destroy(this.sle_output)
destroy(this.st_note)
destroy(this.cb_start)
destroy(this.cb_cancel)
end on

event open;long ll_i
inv_options = Message.PowerObjectParm
if IsNull(inv_options) then
	Close(this)
	return
end if
if not IsValid(inv_options) then
	Close(this)
	return
end if
for ll_i = 1 to UpperBound(inv_options.suite_names)
	ddlb_suite.AddItem(inv_options.suite_names[ll_i])
next
if UpperBound(inv_options.suite_names) > 0 then ddlb_suite.SelectItem(1)
sle_output.Text = inv_options.output_path
end event

event closequery;if IsNull(inv_options) then return 0
if IsValid(inv_options) then
	if not inv_options.accepted then inv_options.accepted = false
end if
return 0
end event

type st_intro from statictext within w_test_setup
integer x = 64
integer y = 48
integer width = 2780
integer height = 140
integer textsize = -10
integer weight = 700
string facename = "Segoe UI"
long backcolor = 79416533
string text = "Choose a typed suite and the JSON result file. Start creates a one-shot JSON request."
end type

type st_suite from statictext within w_test_setup
integer x = 64
integer y = 240
integer width = 500
integer height = 90
integer textsize = -9
string facename = "Segoe UI"
long backcolor = 79416533
string text = "Suite"
end type

type ddlb_suite from dropdownlistbox within w_test_setup
integer x = 600
integer y = 220
integer width = 2240
integer height = 520
integer taborder = 10
integer textsize = -9
string facename = "Segoe UI"
boolean allowedit = false
boolean sorted = false
borderstyle borderstyle = stylelowered!
end type

type st_output from statictext within w_test_setup
integer x = 64
integer y = 400
integer width = 500
integer height = 90
integer textsize = -9
string facename = "Segoe UI"
long backcolor = 79416533
string text = "Result file"
end type

type sle_output from singlelineedit within w_test_setup
integer x = 600
integer y = 380
integer width = 2240
integer height = 110
integer taborder = 20
integer textsize = -9
string facename = "Segoe UI"
borderstyle borderstyle = stylelowered!
end type

type st_note from statictext within w_test_setup
integer x = 64
integer y = 560
integer width = 2780
integer height = 220
integer textsize = -8
string facename = "Segoe UI"
long backcolor = 79416533
string text = "The result file must not already exist. Tests use the environment already prepared by this application."
end type

type cb_start from commandbutton within w_test_setup
integer x = 1930
integer y = 900
integer width = 430
integer height = 120
integer taborder = 30
integer textsize = -9
string facename = "Segoe UI"
string text = "Start"
boolean default = true
end type

event clicked;if IsNull(inv_options) then return
if not IsValid(inv_options) then return
if ddlb_suite.Text = "" then
	MessageBox("pb-test", "Select a test suite.", Exclamation!)
	return
end if
if Trim(sle_output.Text) = "" then
	MessageBox("pb-test", "Enter a result file.", Exclamation!)
	return
end if
inv_options.suite = Lower(ddlb_suite.Text)
inv_options.output_path = Trim(sle_output.Text)
inv_options.accepted = true
Close(Parent)
end event

type cb_cancel from commandbutton within w_test_setup
integer x = 2410
integer y = 900
integer width = 430
integer height = 120
integer taborder = 40
integer textsize = -9
string facename = "Segoe UI"
string text = "Cancel"
boolean cancel = true
end type

event clicked;if not IsNull(inv_options) then
	if IsValid(inv_options) then inv_options.accepted = false
end if
Close(Parent)
end event
