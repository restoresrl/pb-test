$PBExportHeader$n_test_app.sru
$PBExportComments$pb-test: auto-instantiated target adapter; register suites and optional cleanup here
forward
global type n_test_app from n_test_session
end type
end forward

global type n_test_app from n_test_session autoinstantiate
end type

forward prototypes
public function n_test_suite of_suite (string as_name)
public subroutine of_suite_names (ref string as_names[])
public function string of_cleanup ()
end prototypes

public function n_test_suite of_suite (string as_name);n_suite_all lnv_all
n_test_suite lnv_none
choose case as_name
	case "", "n_suite_all"
		lnv_all = create n_suite_all
		return lnv_all
	case else
		SetNull(lnv_none)
		return lnv_none
end choose
end function

public subroutine of_suite_names (ref string as_names[]);// Keep this list in sync with the typed dispatcher above.
as_names[1] = "n_suite_all"
end subroutine

public function string of_cleanup ();// Optional target cleanup. Return an error message on failure, otherwise empty.
return ""
end function

on n_test_app.create
call super::create
end on

on n_test_app.destroy
call super::destroy
end on
