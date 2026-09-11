$PBExportHeader$n_test_example.sru
$PBExportComments$pb-test: example test case. Copy, rename to n_test_<subject>, replace the test_ events
forward
global type n_test_example from n_test_case
end type
end forward

global type n_test_example from n_test_case
event test_string_functions ( )
event test_numbers ( )
event test_dates ( )
event test_that_fails ( )
event test_that_raises ( )
end type
global n_test_example n_test_example

type variables
string is_subject
end variables

event setup;is_subject = "Hello"
end event

event teardown;is_subject = ""
end event

event test_string_functions;of_assert_equal("hello", Lower(is_subject), "Lower")
of_assert_equal(5, Len(is_subject), "Len")
of_assert_true(Pos(is_subject, "ell") = 2, "Pos finds the substring")
end event

event test_numbers;decimal ldec_third
ldec_third = 1.5 * 2
of_assert_equal(3.0, ldec_third, "decimal arithmetic")
of_assert_equal(7, 3 + 4, "long arithmetic")
of_assert_false(1 > 2, "comparison")
end event

event test_dates;date ld_day
ld_day = Date(2026, 9, 11)
of_assert_equal(Date("2026-09-11"), ld_day, "Date() and Date(string) agree")
of_assert_equal(6, DayNumber(ld_day), "2026-09-11 is a Friday")
end event

event test_that_fails;// kept in the template so the first run shows what a failure looks like; delete it
of_assert_equal("expected", "actual", "this assertion is meant to fail")
of_assert_true(false, "and this one too")
end event

event test_that_raises;// kept in the template so the first run shows what a runtime error looks like; delete it
datastore lds_null
lds_null.Reset()
end event

on n_test_example.create
call super::create
TriggerEvent( this, "constructor" )
end on

on n_test_example.destroy
TriggerEvent( this, "destructor" )
call super::destroy
end on
