$PBExportHeader$n_test_report.sru
$PBExportComments$pb-test: collects test outcomes and renders them as JUnit XML and as a text summary
forward
global type n_test_report from nonvisualobject
end type
end forward

global type n_test_report from nonvisualobject
end type
global n_test_report n_test_report

type variables
private string is_suite[]
private string is_case[]
private string is_test[]
private string is_status[]
private string is_message[]
private long il_time_ms[]
private long il_count = 0
private long il_current = 0
private long il_started_ms = 0
end variables

forward prototypes
public subroutine of_begin_test (string as_suite, string as_case, string as_test)
public subroutine of_add_failure (string as_message)
public subroutine of_add_error (string as_message)
public subroutine of_end_test ()
public function long of_count ()
public function long of_count_status (string as_status)
public function string of_status (long al_index)
public function string of_replace_all (string as_text, string as_from, string as_to)
public function string of_xml_escape (string as_text)
public function string of_seconds (long al_ms)
public function string of_junit_xml (string as_name)
public function integer of_write_file (string as_path, string as_content)
public function string of_summary ()
end prototypes

public subroutine of_begin_test (string as_suite, string as_case, string as_test);il_count = il_count + 1
il_current = il_count
is_suite[il_count] = as_suite
is_case[il_count] = as_case
is_test[il_count] = as_test
is_status[il_count] = "pass"
is_message[il_count] = ""
il_time_ms[il_count] = 0
il_started_ms = Cpu()
end subroutine

public subroutine of_add_failure (string as_message);if il_current = 0 then return
if IsNull(as_message) then as_message = "(null message)"
if is_status[il_current] = "pass" then is_status[il_current] = "fail"
if is_message[il_current] <> "" then is_message[il_current] = is_message[il_current] + "~r~n"
is_message[il_current] = is_message[il_current] + as_message
end subroutine

public subroutine of_add_error (string as_message);if il_current = 0 then return
if IsNull(as_message) then as_message = "(null message)"
is_status[il_current] = "error"
if is_message[il_current] <> "" then is_message[il_current] = is_message[il_current] + "~r~n"
is_message[il_current] = is_message[il_current] + as_message
end subroutine

public subroutine of_end_test ();if il_current = 0 then return
il_time_ms[il_current] = Cpu() - il_started_ms
il_current = 0
end subroutine

public function long of_count ();return il_count
end function

public function long of_count_status (string as_status);long ll_i, ll_n = 0
for ll_i = 1 to il_count
	if is_status[ll_i] = as_status then ll_n = ll_n + 1
next
return ll_n
end function

public function string of_status (long al_index);if al_index < 1 or al_index > il_count then return ""
return is_status[al_index]
end function

public function string of_replace_all (string as_text, string as_from, string as_to);long ll_pos, ll_len
if IsNull(as_text) then return ""
ll_len = Len(as_from)
ll_pos = Pos(as_text, as_from)
do while ll_pos > 0
	as_text = Replace(as_text, ll_pos, ll_len, as_to)
	ll_pos = Pos(as_text, as_from, ll_pos + Len(as_to))
loop
return as_text
end function

public function string of_xml_escape (string as_text);if IsNull(as_text) then return ""
as_text = of_replace_all(as_text, "&", "&amp;")
as_text = of_replace_all(as_text, "<", "&lt;")
as_text = of_replace_all(as_text, ">", "&gt;")
as_text = of_replace_all(as_text, '"', "&quot;")
return as_text
end function

public function string of_seconds (long al_ms);// locale-independent "s.mmm": String() would use the locale decimal separator
long ll_s, ll_ms
if al_ms < 0 then al_ms = 0
ll_s = Int(al_ms / 1000)
ll_ms = al_ms - ll_s * 1000
return String(ll_s) + "." + Right("000" + String(ll_ms), 3)
end function

public function string of_junit_xml (string as_name);string ls_xml, ls_suites[], ls_suite, ls_nl
long ll_i, ll_j, ll_n = 0, ll_tests, ll_fail, ll_err, ll_ms, ll_total_ms = 0
boolean lb_seen
ls_nl = "~r~n"
for ll_i = 1 to il_count
	lb_seen = false
	for ll_j = 1 to ll_n
		if ls_suites[ll_j] = is_suite[ll_i] then lb_seen = true
	next
	if not lb_seen then
		ll_n = ll_n + 1
		ls_suites[ll_n] = is_suite[ll_i]
	end if
	ll_total_ms = ll_total_ms + il_time_ms[ll_i]
next
ls_xml = '<?xml version="1.0" encoding="UTF-8"?>' + ls_nl
ls_xml = ls_xml + '<testsuites name="' + of_xml_escape(as_name) + '" tests="' + String(il_count) + &
	'" failures="' + String(of_count_status("fail")) + '" errors="' + String(of_count_status("error")) + &
	'" time="' + of_seconds(ll_total_ms) + '">' + ls_nl
for ll_j = 1 to ll_n
	ls_suite = ls_suites[ll_j]
	ll_tests = 0
	ll_fail = 0
	ll_err = 0
	ll_ms = 0
	for ll_i = 1 to il_count
		if is_suite[ll_i] <> ls_suite then continue
		ll_tests = ll_tests + 1
		ll_ms = ll_ms + il_time_ms[ll_i]
		if is_status[ll_i] = "fail" then ll_fail = ll_fail + 1
		if is_status[ll_i] = "error" then ll_err = ll_err + 1
	next
	ls_xml = ls_xml + '  <testsuite name="' + of_xml_escape(ls_suite) + '" tests="' + String(ll_tests) + &
		'" failures="' + String(ll_fail) + '" errors="' + String(ll_err) + '" time="' + of_seconds(ll_ms) + '">' + ls_nl
	for ll_i = 1 to il_count
		if is_suite[ll_i] <> ls_suite then continue
		ls_xml = ls_xml + '    <testcase classname="' + of_xml_escape(is_case[ll_i]) + '" name="' + &
			of_xml_escape(is_test[ll_i]) + '" time="' + of_seconds(il_time_ms[ll_i]) + '"'
		choose case is_status[ll_i]
			case "fail"
				ls_xml = ls_xml + '>' + ls_nl + '      <failure message="' + of_xml_escape(is_message[ll_i]) + '">' + &
					of_xml_escape(is_message[ll_i]) + '</failure>' + ls_nl + '    </testcase>' + ls_nl
			case "error"
				ls_xml = ls_xml + '>' + ls_nl + '      <error message="' + of_xml_escape(is_message[ll_i]) + '">' + &
					of_xml_escape(is_message[ll_i]) + '</error>' + ls_nl + '    </testcase>' + ls_nl
			case else
				ls_xml = ls_xml + '/>' + ls_nl
		end choose
	next
	ls_xml = ls_xml + '  </testsuite>' + ls_nl
next
ls_xml = ls_xml + '</testsuites>' + ls_nl
return ls_xml
end function

public function integer of_write_file (string as_path, string as_content);integer li_file
li_file = FileOpen(as_path, TextMode!, Write!, LockWrite!, Replace!, EncodingUTF8!)
if li_file < 0 then return -1
if FileWriteEx(li_file, as_content) < 0 then
	FileClose(li_file)
	return -1
end if
FileClose(li_file)
return 1
end function

public function string of_summary ();string ls_text
long ll_i
ls_text = "pb-test: " + String(il_count) + " tests, " + String(of_count_status("pass")) + " passed, " + &
	String(of_count_status("fail")) + " failed, " + String(of_count_status("error")) + " errors"
for ll_i = 1 to il_count
	if is_status[ll_i] = "pass" then continue
	ls_text = ls_text + "~r~n" + Upper(is_status[ll_i]) + " " + is_case[ll_i] + "." + is_test[ll_i] + ": " + is_message[ll_i]
next
return ls_text
end function

on n_test_report.create
call super::create
TriggerEvent( this, "constructor" )
end on

on n_test_report.destroy
TriggerEvent( this, "destructor" )
call super::destroy
end on
