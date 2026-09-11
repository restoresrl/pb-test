$PBExportHeader$n_test_runner.sru
$PBExportComments$pb-test: runs a suite, writes the JUnit XML, reads /suite= /out= /exit from the command line
forward
global type n_test_runner from nonvisualobject
end type
end forward

global type n_test_runner from nonvisualobject
end type
global n_test_runner n_test_runner

type prototypes
subroutine ExitProcess (ulong uExitCode) library "kernel32.dll"
end prototypes

type variables
protected n_test_report inv_report
protected string is_out_path
protected string is_summary = ""
protected long il_failed = -1
end variables

forward prototypes
public function long of_run (n_test_suite anv_suite, string as_name, string as_out_path)
public function long of_run_from_commandline (n_test_suite anv_default_suite)
public function string of_option (string as_parm, string as_name, string as_default)
public function string of_summary ()
public function long of_failed ()
end prototypes

public function long of_run (n_test_suite anv_suite, string as_name, string as_out_path);// runs anv_suite (and destroys it), writes the JUnit XML to as_out_path when not empty
long ll_failed
boolean lb_ok = true
if IsValid(inv_report) then destroy inv_report
inv_report = create n_test_report
is_out_path = as_out_path
if IsNull(anv_suite) then lb_ok = false
if lb_ok then
	if not IsValid(anv_suite) then lb_ok = false
end if
if not lb_ok then
	inv_report.of_begin_test(as_name, "(runner)", "(create)")
	inv_report.of_add_error("no suite to run: '" + as_name + "' is null or invalid. A suite selected by name must survive the link: deploy its PBL as a PBD, or list it in a PBR")
	inv_report.of_end_test()
	ll_failed = 1
else
	ll_failed = anv_suite.of_run(inv_report)
	destroy anv_suite
end if
is_summary = inv_report.of_summary()
if not IsNull(as_out_path) and as_out_path <> "" then
	if inv_report.of_write_file(as_out_path, inv_report.of_junit_xml(as_name)) < 0 then
		is_summary = is_summary + "~r~ncould not write " + as_out_path
		ll_failed = ll_failed + 1
	end if
end if
il_failed = ll_failed
return ll_failed
end function

public function long of_run_from_commandline (n_test_suite anv_default_suite);// /suite=<class>  /out=<path>  /exit
// without /out the XML goes to <appname>.test.result.xml in the current directory
// /suite= picks a suite by class name; that only works when the class survived the link (PBD or PBR)
string ls_parm, ls_suite, ls_out
boolean lb_exit
n_test_suite lnv_suite
ls_parm = CommandParm()
if IsNull(ls_parm) then ls_parm = ""
ls_suite = of_option(ls_parm, "suite", "")
ls_out = of_option(ls_parm, "out", Lower(GetApplication().AppName) + ".test.result.xml")
lb_exit = Pos(Lower(ls_parm), "/exit") > 0
if ls_suite = "" then
	lnv_suite = anv_default_suite
	if IsValid(anv_default_suite) then ls_suite = Lower(ClassName(anv_default_suite))
else
	if IsValid(anv_default_suite) then destroy anv_default_suite
	try
		lnv_suite = create using ls_suite
	catch (RuntimeError lre_create)
		SetNull(lnv_suite)
	end try
end if
of_run(lnv_suite, ls_suite, ls_out)
if Handle(GetApplication()) = 0 and not lb_exit then MessageBox("pb-test", is_summary)
if lb_exit then ExitProcess(il_failed)
return il_failed
end function

public function string of_option (string as_parm, string as_name, string as_default);string ls_lower
long ll_pos, ll_end
ls_lower = Lower(as_parm)
ll_pos = Pos(ls_lower, "/" + Lower(as_name) + "=")
if ll_pos = 0 then return as_default
ll_pos = ll_pos + Len(as_name) + 2
if Mid(as_parm, ll_pos, 1) = '"' then
	ll_end = Pos(as_parm, '"', ll_pos + 1)
	if ll_end = 0 then ll_end = Len(as_parm) + 1
	return Mid(as_parm, ll_pos + 1, ll_end - ll_pos - 1)
end if
ll_end = Pos(as_parm, " ", ll_pos)
if ll_end = 0 then ll_end = Len(as_parm) + 1
return Mid(as_parm, ll_pos, ll_end - ll_pos)
end function

public function string of_summary ();return is_summary
end function

public function long of_failed ();return il_failed
end function

on n_test_runner.create
call super::create
TriggerEvent( this, "constructor" )
end on

on n_test_runner.destroy
TriggerEvent( this, "destructor" )
call super::destroy
end on
