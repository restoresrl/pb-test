$PBExportHeader$n_test_request.sru
$PBExportComments$pb-test: one-shot JSON request, captured before application initialization
forward
global type n_test_request from nonvisualobject
end type
end forward

global type n_test_request from nonvisualobject
end type
global n_test_request n_test_request

type prototypes
function boolean MoveFileW (string existing_name, string new_name) library "kernel32.dll"
subroutine GetSystemTimeAsFileTime (ref longlong file_time) library "kernel32.dll"
end prototypes

type variables
public string request_id = ""
public string application = ""
public string suite = ""
public string output_path = ""
public string error_text = ""
public string startup_dir = ""
public boolean requested = false
private string is_pending
private string is_active
private boolean ib_interactive = false
private boolean ib_owns_interactive_control = false
end variables

forward prototypes
public function integer of_acquire ()
public function integer of_prepare_interactive (string as_suite, string as_output)
public subroutine of_release_interactive ()
public function string of_default_output ()
private subroutine of_paths ()
private function integer of_load ()
private function boolean of_name (string as_name)
end prototypes

private subroutine of_paths ();startup_dir = GetCurrentDirectory()
application = Lower(ClassName(GetApplication()))
is_pending = startup_dir + "\" + application + "_test.json"
is_active = is_pending + ".active"
end subroutine

public function string of_default_output ();longlong lll_filetime
of_paths()
GetSystemTimeAsFileTime(lll_filetime)
return startup_dir + "\" + application + "_test_result_" + String(lll_filetime, "0") + ".json"
end function

public function integer of_prepare_interactive (string as_suite, string as_output);JSONGenerator lnv_json
n_test_report lnv_report
long ll_root
longlong lll_filetime
string ls_json, ls_temp
integer li_write
of_paths()
requested = true
ib_interactive = true
suite = Lower(as_suite)
output_path = as_output
if suite = "" or not of_name(suite) then
	error_text = "Invalid interactive suite name"
	return -1
end if
if Trim(output_path) = "" then
	error_text = "Empty interactive output path"
	return -1
end if
if DirectoryExists(is_pending + ".lock") or FileExists(is_pending) or FileExists(is_active) then
	error_text = "Another test request already owns this application and startup directory"
	return -1
end if
GetSystemTimeAsFileTime(lll_filetime)
request_id = "manual_" + String(lll_filetime, "0")
ls_temp = is_pending + "." + request_id + ".tmp"
lnv_json = create JSONGenerator
lnv_report = create n_test_report
try
	ll_root = lnv_json.CreateJsonObject()
	lnv_json.AddItemNumber(ll_root, "schema_version", 1)
	lnv_json.AddItemString(ll_root, "request_id", request_id)
	lnv_json.AddItemString(ll_root, "application", application)
	lnv_json.AddItemString(ll_root, "suite", suite)
	lnv_json.AddItemString(ll_root, "output", output_path)
	lnv_json.AddItemNumber(ll_root, "expires_at", LongLong((Double(lll_filetime) - 116444736000000000) / 10000000) + 3600)
	ls_json = lnv_json.GetJsonString()
	li_write = lnv_report.of_write_file(ls_temp, ls_json)
	if li_write < 0 then
		error_text = "Could not write interactive test request: " + ls_temp
		return -1
	end if
	if not MoveFileW(ls_temp, is_pending) then
		FileDelete(ls_temp)
		error_text = "Could not publish interactive test request: " + is_pending
		return -1
	end if
	ib_owns_interactive_control = true
finally
	destroy lnv_json
	destroy lnv_report
end try
return of_acquire()
end function

public subroutine of_release_interactive ();if not ib_interactive then return
if not ib_owns_interactive_control then return
if FileExists(is_pending) then FileDelete(is_pending)
if FileExists(is_active) then FileDelete(is_active)
end subroutine

public function integer of_acquire ();// 0: normal launch; 1: acquired; -1: blocked. Call once before test initialization.
integer li_result
JSONGenerator lnv_json
n_test_report lnv_report
long ll_root
li_result = of_load()
if li_result < 0 then
	lnv_json = create JSONGenerator
	lnv_report = create n_test_report
	ll_root = lnv_json.CreateJsonObject()
	lnv_json.AddItemNumber(ll_root, "schema_version", 1)
	lnv_json.AddItemString(ll_root, "error", error_text)
	lnv_report.of_publish(is_active + ".error.json", lnv_json.GetJsonString())
	destroy lnv_json
	destroy lnv_report
end if
return li_result
end function

private function integer of_load ();JSONParser lnv_json
long ll_root, ll_i, ll_j
longlong lll_filetime
double ld_now, ld_expiry
string ls_error, ls_key, ls_previous[], ls_text
blob lbl_data
integer li_file
of_paths()
if FileExists(is_active) then
	requested = true
	error_text = "An active test request already exists: " + is_active
	return -1
end if
if not FileExists(is_pending) then return 0
requested = true
if not MoveFileW(is_pending, is_active) then
	error_text = "Could not acquire test request: " + is_pending
	return -1
end if
lnv_json = create JSONParser
try
	li_file = FileOpen(is_active, StreamMode!, Read!, Shared!)
	if li_file < 0 then
		error_text = "Could not open test request"
		return -1
	end if
	if FileReadEx(li_file, lbl_data) < 0 then
		FileClose(li_file)
		error_text = "Could not read test request"
		return -1
	end if
	FileClose(li_file)
	ls_text = String(lbl_data, EncodingUTF8!)
	if Left(ls_text, 1) = Char(65279) then ls_text = Mid(ls_text, 2)
	ls_error = lnv_json.LoadString(ls_text)
	if IsNull(ls_error) then ls_error = "JSON parser returned null"
	if ls_error <> "" then
		error_text = "Invalid test request JSON: " + ls_error
		return -1
	end if
	ll_root = lnv_json.GetRootItem()
	if lnv_json.GetItemType(ll_root) <> JsonObjectItem! then
		error_text = "Test request must be an object"
		return -1
	end if
	for ll_i = 1 to lnv_json.GetChildCount(ll_root)
		ls_key = lnv_json.GetChildKey(ll_root, ll_i)
		for ll_j = 1 to ll_i - 1
			if ls_previous[ll_j] = ls_key then
				error_text = "Duplicate request key: " + ls_key
				return -1
			end if
		next
		ls_previous[ll_i] = ls_key
		choose case ls_key
			case "schema_version", "expires_at"
				if lnv_json.GetItemType(ll_root, ls_key) <> JsonNumberItem! then
					error_text = "Request field must be numeric: " + ls_key
					return -1
				end if
			case "request_id", "application", "suite", "output"
				if lnv_json.GetItemType(ll_root, ls_key) <> JsonStringItem! then
					error_text = "Request field must be a string: " + ls_key
					return -1
				end if
			case else
				error_text = "Unknown request field: " + ls_key
				return -1
		end choose
	next
	if not lnv_json.ContainsKey(ll_root, "schema_version") or not lnv_json.ContainsKey(ll_root, "request_id") or &
		not lnv_json.ContainsKey(ll_root, "application") or not lnv_json.ContainsKey(ll_root, "output") or &
		not lnv_json.ContainsKey(ll_root, "expires_at") then
		error_text = "Missing required test request fields"
		return -1
	end if
	if lnv_json.GetItemNumber(ll_root, "schema_version") <> 1 then
		error_text = "Unsupported test request schema_version"
		return -1
	end if
	if lnv_json.GetItemString(ll_root, "application") <> application then
		error_text = "Test request is for a different application"
		return -1
	end if
	request_id = lnv_json.GetItemString(ll_root, "request_id")
	if not of_name("r" + request_id) then
		error_text = "Invalid request_id"
		return -1
	end if
	if request_id = "" then
		error_text = "Empty request_id"
		return -1
	end if
	if lnv_json.ContainsKey(ll_root, "suite") then suite = lnv_json.GetItemString(ll_root, "suite")
	if suite <> "" then
		if not of_name(suite) then
			error_text = "Invalid suite name"
			return -1
		end if
	end if
	GetSystemTimeAsFileTime(lll_filetime)
	ld_now = (Double(lll_filetime) - 116444736000000000) / 10000000
	ld_expiry = lnv_json.GetItemNumber(ll_root, "expires_at")
	if ld_expiry <= ld_now or ld_expiry <> LongLong(ld_expiry) then
		error_text = "Test request has expired or expires_at is invalid (now=" + String(ld_now, "0") + ", expiry=" + String(ld_expiry, "0") + ")"
		return -1
	end if
	output_path = lnv_json.GetItemString(ll_root, "output")
	if output_path = "" then
		error_text = "Empty output path"
		return -1
	end if
	// Only drive-qualified and UNC paths are absolute. Relative paths use startup_dir.
	if Left(output_path, 2) <> "\\" and Mid(output_path, 2, 2) <> ":\" then
		output_path = startup_dir + "\" + output_path
	end if
	if FileExists(output_path) or FileExists(output_path + ".tmp") then
		error_text = "Output already exists: " + output_path
		return -1
	end if
catch (Throwable lth_error)
	error_text = "Could not load test request: " + lth_error.GetMessage()
	return -1
finally
	destroy lnv_json
end try
return 1
end function

private function boolean of_name (string as_name);long ll_i
string ls_char
if IsNull(as_name) or as_name = "" then return false
for ll_i = 1 to Len(as_name)
	ls_char = Mid(as_name, ll_i, 1)
	if Pos("abcdefghijklmnopqrstuvwxyz_", ls_char) > 0 then continue
	if ll_i > 1 and Pos("0123456789", ls_char) > 0 then continue
	return false
next
return true
end function

on n_test_request.create
call super::create
TriggerEvent( this, "constructor" )
end on

on n_test_request.destroy
TriggerEvent( this, "destructor" )
call super::destroy
end on
