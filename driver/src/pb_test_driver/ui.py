"""Look at and act on the windows of a running PowerBuilder application.

Everything goes through pywinauto's `uia` backend. What PowerBuilder 2022 R3
exposes once `ACCESSIBILITY=1` is on (observed, not documented by Appeon):

- a window is a `Window` of class `FNWND3`, named after its title;
- every control has `automation_id` equal to its PowerBuilder control id
  (`1000`, `1001`, ... in `Control[]` order) and is named by `accessiblename`,
  or by `text` for buttons and static text;
- a DataWindow is a child `Window` named by `accessiblename` or "Datawindow".
  Its children are one `Text` per header or label and one `Edit` per cell, named
  after the column. Rows are not in the tree; `read` groups cells by the top
  edge of their rectangle;
- the cell's `ValuePattern` returns the formatted display value. `SetValue` on a
  cell does nothing, so `type_text` on a DataWindow cell goes through the keyboard.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from pb_test_driver import run as _run

SELECTOR_KEYS = {
    "auto_id",
    "title",
    "title_re",
    "control_type",
    "class_name",
    "found_index",
    "within",
}


def _app(run_id: str) -> Any:
    from pywinauto import Application

    run = _run.get(run_id)
    return Application(backend="uia").connect(process=run.pid, timeout=10)


def _window(run_id: str, window: str | None) -> Any:
    """Top-level window of the run: exact title, `re:<regex>`, or the top window when None."""
    app = _app(run_id)
    if window is None:
        return app.top_window()
    if window.startswith("re:"):
        return app.window(title_re=window[3:])
    return app.window(title=window)


def _resolve(run_id: str, window: str | None, selector: dict[str, Any] | None) -> Any:
    """A control under the window. `within` nests a selector: the parent is resolved first.

    DataWindow cells reuse `auto_id` 1, 2, 3 ... in every DataWindow, so a cell is
    addressed as `{"within": {"auto_id": "1002"}, "auto_id": "5"}`.
    """
    win = _window(run_id, window)
    if not selector:
        return win
    bad = set(selector) - SELECTOR_KEYS
    if bad:
        raise ValueError(f"unknown selector keys {sorted(bad)}; allowed: {sorted(SELECTOR_KEYS)}")
    sel = dict(selector)
    parent = win
    within = sel.pop("within", None)
    if within:
        parent = _resolve(run_id, window, within)
    if "auto_id" in sel:
        sel["auto_id"] = str(sel["auto_id"])
    return parent.child_window(**sel)


def _rect(el: Any) -> dict[str, int]:
    r = el.rectangle()
    return {"left": r.left, "top": r.top, "right": r.right, "bottom": r.bottom}


def _describe(el: Any) -> dict[str, Any]:
    info = el.element_info
    return {
        "control_type": info.control_type,
        "name": info.name,
        "auto_id": info.automation_id,
        "class_name": info.class_name,
        "rect": _rect(el),
    }


def windows(run_id: str) -> list[dict[str, Any]]:
    """Top-level windows of the process, UIA view plus any runtime error dialog."""
    from pywinauto import findwindows

    run = _run.get(run_id)
    out: list[dict[str, Any]] = []
    for el in findwindows.find_elements(process=run.pid, backend="uia", top_level_only=True):
        out.append(
            {
                "title": el.name,
                "class_name": el.class_name,
                "control_type": el.control_type,
                "handle": el.handle,
            }
        )
    err = _run.find_error_dialog(run.pid)
    if err is not None:
        out.append(
            {
                "title": err["title"],
                "class_name": "#32770",
                "control_type": "Dialog",
                "runtime_error": err,
            }
        )
    return out


def controls(
    run_id: str, window: str | None = None, selector: dict[str, Any] | None = None, depth: int = 6
) -> list[dict[str, Any]]:
    """Flat list of the control tree under a window or a selected control, with nesting level."""
    root = _resolve(run_id, window, selector)
    root = root.wrapper_object() if hasattr(root, "wrapper_object") else root
    out: list[dict[str, Any]] = []

    def walk(el: Any, level: int) -> None:
        d = _describe(el)
        d["level"] = level
        out.append(d)
        if level >= depth:
            return
        for child in el.children():
            walk(child, level + 1)

    walk(root, 0)
    return out


def rows_from_cells(cells: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Group DataWindow cells into rows by the top edge of their rectangle.

    `cells` are dicts with `name`, `value`, `top`, `left`. Pure so it can be tested
    without a live application.
    """
    by_top: dict[int, list[dict[str, Any]]] = {}
    for c in cells:
        by_top.setdefault(int(c["top"]), []).append(c)
    rows: list[dict[str, str]] = []
    for top in sorted(by_top):
        row: dict[str, str] = {}
        for c in sorted(by_top[top], key=lambda c: int(c["left"])):
            name = str(c["name"]) or f"col{len(row) + 1}"
            if name in row:
                name = f"{name}_{len(row) + 1}"
            row[name] = str(c["value"])
        rows.append(row)
    return rows


def _value(el: Any) -> str:
    try:
        return str(el.get_value())
    except Exception:
        try:
            return str(el.legacy_properties().get("Value", ""))
        except Exception:
            return ""


def read(
    run_id: str, window: str | None = None, selector: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Read values. DataWindow rows are visual groups, not logical database rows."""
    el = _resolve(run_id, window, selector).wrapper_object()
    d = _describe(el)
    children = el.children()
    edits = [c for c in children if c.element_info.control_type == "Edit"]
    texts = [c for c in children if c.element_info.control_type == "Text"]
    if edits and (d["control_type"] in ("Window", "Pane", "Custom") or len(edits) > 1):
        cells = [
            {
                "name": c.element_info.name,
                "value": _value(c),
                "top": c.rectangle().top,
                "left": c.rectangle().left,
            }
            for c in edits
        ]
        d["kind"] = "datawindow"
        d["labels"] = [t.element_info.name for t in texts]
        d["cells"] = cells
        d["rows"] = rows_from_cells(cells)
        d["visual_row_count"] = len(d["rows"])
        d["row_grouping"] = "rectangle_top"
        d["rows_are_logical"] = False
        return d
    d["kind"] = "control"
    d["text"] = el.window_text()
    d["value"] = _value(el)
    return d


def click(
    run_id: str, window: str | None, selector: dict[str, Any], method: str = "invoke"
) -> dict[str, Any]:
    """`invoke` uses the UIA Invoke pattern, `mouse` a real click. Both fire `clicked`."""
    win = _window(run_id, window)
    win.set_focus()
    el = _resolve(run_id, window, selector).wrapper_object()
    if method == "invoke":
        try:
            el.invoke()
        except Exception:
            el.click_input()
    elif method == "mouse":
        el.click_input()
    else:
        raise ValueError("method must be 'invoke' or 'mouse'")
    time.sleep(0.3)
    return _describe(el)


def literal_keys(text: str) -> str:
    """Escape pywinauto key syntax so caller text cannot become shortcuts."""
    return "".join("{" + c + "}" if c in "+^%~(){}" else c for c in text)


def type_text(
    run_id: str,
    window: str | None,
    selector: dict[str, Any],
    text: str,
    method: str = "auto",
    clear: bool = True,
    tab_out: bool = False,
) -> dict[str, Any]:
    """Put `text` into an edit control.

    `value` sets it through the ValuePattern (works on a SingleLineEdit, not on a
    DataWindow cell); `keys` clicks the control and types (works everywhere, honours
    edit masks and validation); `auto` tries `value` and falls back to `keys` when the
    value did not take. `tab_out` sends TAB afterwards so a DataWindow accepts the cell.
    """
    if method not in ("auto", "value", "keys"):
        raise ValueError("method must be 'auto', 'value' or 'keys'")
    if not clear and method == "value":
        raise ValueError("method='value' replaces text; use 'keys' when clear=False")
    from pywinauto import keyboard

    win = _window(run_id, window)
    win.set_focus()
    el = _resolve(run_id, window, selector).wrapper_object()
    used = "keys" if not clear else method
    # PB's cell ValuePattern can partially change text before reporting
    # failure. Do not attempt it and then type the same text a second time.
    if el.parent().class_name().lower().startswith("pbdw"):
        if method == "value":
            raise ValueError("DataWindow cells require method='keys' or 'auto'")
        used = "keys"
    if used in ("value", "auto"):
        try:
            el.set_edit_text(text)
        except Exception:
            used = "keys" if method == "auto" else method
        else:
            time.sleep(0.2)
            if _value(el) == text:
                used = "value"
            elif method == "auto":
                used = "keys"
    if used == "keys":
        el.click_input()
        time.sleep(0.2)
        if clear:
            keyboard.send_keys("^a{BACKSPACE}")
        keyboard.send_keys(
            literal_keys(text), with_spaces=True, with_tabs=False, with_newlines=False
        )
    if tab_out:
        keyboard.send_keys("{TAB}")
    time.sleep(0.3)
    d = _describe(el)
    d["method"] = used
    d["value"] = _value(el)
    return d


def screenshot(
    run_id: str, path: str | Path, window: str | None = None, selector: dict[str, Any] | None = None
) -> dict[str, Any]:
    el = _resolve(run_id, window, selector).wrapper_object()
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    el.capture_as_image().save(out)
    return {"path": str(out), **_describe(el)}


def close_window(run_id: str, window: str | None = None) -> dict[str, Any]:
    win = _window(run_id, window)
    d = _describe(win.wrapper_object())
    win.close()
    return d
