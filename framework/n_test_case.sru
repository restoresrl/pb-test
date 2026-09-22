$PBExportHeader$n_test_case.sru
$PBExportComments$pb-test: base class for test cases. Inherit, add test_* events, use of_assert_*
forward
global type n_test_case from nonvisualobject
end type
end forward

global type n_test_case from nonvisualobject
event setup ( )
event teardown ( )
end type
global n_test_case n_test_case

type variables
protected n_test_report inv_report
protected string is_suite_name
end variables

forward prototypes
public function long of_run (n_test_report anv_report, string as_suite)
protected subroutine of_discover (ref string as_tests[])
protected function string of_describe_error (runtimeerror are_error)
protected subroutine of_compare (boolean ab_null_expected, boolean ab_null_actual, boolean ab_equal, string as_expected, string as_actual, string as_message)
public subroutine of_fail (string as_message)
public subroutine of_progress (string as_message)
public subroutine of_assert_true (boolean ab_condition, string as_message)
public subroutine of_assert_false (boolean ab_condition, string as_message)
public subroutine of_assert_equal (string as_expected, string as_actual, string as_message)
public subroutine of_assert_equal (long al_expected, long al_actual, string as_message)
public subroutine of_assert_equal (decimal adec_expected, decimal adec_actual, string as_message)
public subroutine of_assert_equal (double adbl_expected, double adbl_actual, string as_message)
public subroutine of_assert_equal (boolean ab_expected, boolean ab_actual, string as_message)
public subroutine of_assert_equal (date ad_expected, date ad_actual, string as_message)
public subroutine of_assert_equal (datetime adt_expected, datetime adt_actual, string as_message)
public subroutine of_assert_null (any aa_value, string as_message)
public subroutine of_assert_not_null (any aa_value, string as_message)
end prototypes

public function long of_run (n_test_report anv_report, string as_suite);string ls_tests[]
string ls_case
long ll_i, ll_failed = 0
inv_report = anv_report
is_suite_name = as_suite
ls_case = Lower(ClassName(this))
of_discover(ls_tests)
inv_report.of_begin_case(Max(1, UpperBound(ls_tests)))
if UpperBound(ls_tests) = 0 then
	inv_report.of_begin_test(as_suite, ls_case, "(discovery)")
	inv_report.of_add_error("test case declares no test_* events")
	inv_report.of_end_test()
	return 1
end if
for ll_i = 1 to UpperBound(ls_tests)
	inv_report.of_begin_test(as_suite, ls_case, ls_tests[ll_i])
	try
		this.event setup()
		this.TriggerEvent(ls_tests[ll_i])
	catch (RuntimeError lre_test)
		inv_report.of_add_error(of_describe_error(lre_test))
	catch (Throwable lth_test)
		inv_report.of_add_error(lth_test.GetMessage())
	finally
		try
			this.event teardown()
		catch (RuntimeError lre_teardown)
			inv_report.of_add_error("teardown: " + of_describe_error(lre_teardown))
		catch (Throwable lth_teardown)
			inv_report.of_add_error("teardown: " + lth_teardown.GetMessage())
		end try
	end try
	if inv_report.of_status(inv_report.of_count()) <> "pass" then ll_failed = ll_failed + 1
	inv_report.of_end_test()
next
return ll_failed
end function

protected subroutine of_discover (ref string as_tests[]);// every event whose name starts with test_ and that has a script, on this class or an ancestor below n_test_case
ClassDefinition lcd_class
ScriptDefinition lsd_script
long ll_i, ll_j, ll_n = 0
string ls_name
boolean lb_seen
lcd_class = this.ClassDefinition
do while IsValid(lcd_class)
	if Lower(lcd_class.Name) = "n_test_case" then exit
	for ll_i = 1 to UpperBound(lcd_class.ScriptList)
		lsd_script = lcd_class.ScriptList[ll_i]
		if lsd_script.Kind <> ScriptEvent! then continue
		if not lsd_script.IsScripted then continue
		ls_name = Lower(lsd_script.Name)
		if Left(ls_name, 5) <> "test_" then continue
		lb_seen = false
		for ll_j = 1 to ll_n
			if as_tests[ll_j] = ls_name then lb_seen = true
		next
		if not lb_seen then
			ll_n = ll_n + 1
			as_tests[ll_n] = ls_name
		end if
	next
	lcd_class = lcd_class.Ancestor
loop
end subroutine

protected function string of_describe_error (runtimeerror are_error);// GetMessage() already reads "... at line N in <event> of object <class>"; only add the location when it is missing
string ls_text
ls_text = are_error.GetMessage()
if IsNull(ls_text) or ls_text = "" then
	ls_text = "runtime error " + String(are_error.Number) + " at line " + String(are_error.Line) + " in " + are_error.RoutineName + " of object " + are_error.Class
end if
return ls_text
end function

protected subroutine of_compare (boolean ab_null_expected, boolean ab_null_actual, boolean ab_equal, string as_expected, string as_actual, string as_message);string ls_prefix
if IsNull(as_message) or as_message = "" then
	ls_prefix = ""
else
	ls_prefix = as_message + ": "
end if
if ab_null_expected and ab_null_actual then return
if ab_null_expected then
	of_fail(ls_prefix + "expected null but was '" + as_actual + "'")
	return
end if
if ab_null_actual then
	of_fail(ls_prefix + "expected '" + as_expected + "' but was null")
	return
end if
if IsNull(ab_equal) or not ab_equal then of_fail(ls_prefix + "expected '" + as_expected + "' but was '" + as_actual + "'")
end subroutine

public subroutine of_progress (string as_message);// Cooperative checkpoint: changes UI text, never counts or results.
if IsValid(inv_report) then inv_report.of_note(as_message)
end subroutine

public subroutine of_fail (string as_message);if IsValid(inv_report) then inv_report.of_add_failure(as_message)
end subroutine

public subroutine of_assert_true (boolean ab_condition, string as_message);if IsNull(ab_condition) then
	of_fail(as_message + ": condition is null")
elseif not ab_condition then
	of_fail(as_message)
end if
end subroutine

public subroutine of_assert_false (boolean ab_condition, string as_message);if IsNull(ab_condition) then
	of_fail(as_message + ": condition is null")
elseif ab_condition then
	of_fail(as_message)
end if
end subroutine

public subroutine of_assert_equal (string as_expected, string as_actual, string as_message);of_compare(IsNull(as_expected), IsNull(as_actual), as_expected = as_actual, as_expected, as_actual, as_message)
end subroutine

public subroutine of_assert_equal (long al_expected, long al_actual, string as_message);of_compare(IsNull(al_expected), IsNull(al_actual), al_expected = al_actual, String(al_expected), String(al_actual), as_message)
end subroutine

public subroutine of_assert_equal (decimal adec_expected, decimal adec_actual, string as_message);of_compare(IsNull(adec_expected), IsNull(adec_actual), adec_expected = adec_actual, String(adec_expected), String(adec_actual), as_message)
end subroutine

public subroutine of_assert_equal (double adbl_expected, double adbl_actual, string as_message);of_compare(IsNull(adbl_expected), IsNull(adbl_actual), adbl_expected = adbl_actual, String(adbl_expected), String(adbl_actual), as_message)
end subroutine

public subroutine of_assert_equal (boolean ab_expected, boolean ab_actual, string as_message);of_compare(IsNull(ab_expected), IsNull(ab_actual), ab_expected = ab_actual, String(ab_expected), String(ab_actual), as_message)
end subroutine

public subroutine of_assert_equal (date ad_expected, date ad_actual, string as_message);of_compare(IsNull(ad_expected), IsNull(ad_actual), ad_expected = ad_actual, String(ad_expected, "yyyy-mm-dd"), String(ad_actual, "yyyy-mm-dd"), as_message)
end subroutine

public subroutine of_assert_equal (datetime adt_expected, datetime adt_actual, string as_message);of_compare(IsNull(adt_expected), IsNull(adt_actual), adt_expected = adt_actual, String(adt_expected, "yyyy-mm-dd hh:mm:ss"), String(adt_actual, "yyyy-mm-dd hh:mm:ss"), as_message)
end subroutine

public subroutine of_assert_null (any aa_value, string as_message);if not IsNull(aa_value) then of_fail(as_message + ": expected null but was '" + String(aa_value) + "'")
end subroutine

public subroutine of_assert_not_null (any aa_value, string as_message);if IsNull(aa_value) then of_fail(as_message + ": expected a value but was null")
end subroutine

on n_test_case.create
call super::create
TriggerEvent( this, "constructor" )
end on

on n_test_case.destroy
TriggerEvent( this, "destructor" )
call super::destroy
end on
