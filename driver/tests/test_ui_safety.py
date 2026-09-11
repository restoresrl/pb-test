from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from pb_test_driver import ui


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("normal text", "normal text"),
        ("a+b^c%", "a{+}b{^}c{%}"),
        ("{ENTER}", "{{}ENTER{}}"),
        ("(x)~", "{(}x{)}{~}"),
    ],
)
def test_keyboard_input_is_literal(text: str, expected: str) -> None:
    assert ui.literal_keys(text) == expected


def test_invalid_method_rejected_without_connecting() -> None:
    with pytest.raises(ValueError, match="method must"):
        ui.type_text("not-a-run", None, {}, "text", method="typo")


def test_value_cannot_silently_replace_when_append_requested() -> None:
    with pytest.raises(ValueError, match="replaces text"):
        ui.type_text("not-a-run", None, {}, "text", method="value", clear=False)


def test_datawindow_auto_never_attempts_value_pattern(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    el = SimpleNamespace(
        parent=lambda: SimpleNamespace(class_name=lambda: "pbdw"),
        click_input=lambda: calls.append("click"),
        set_edit_text=lambda text: calls.append("unexpected ValuePattern"),
    )
    monkeypatch.setitem(
        sys.modules,
        "pywinauto",
        SimpleNamespace(
            keyboard=SimpleNamespace(send_keys=lambda text, **kwargs: calls.append(text))
        ),
    )
    monkeypatch.setattr(ui, "_window", lambda *args: SimpleNamespace(set_focus=lambda: None))
    monkeypatch.setattr(ui, "_resolve", lambda *args: SimpleNamespace(wrapper_object=lambda: el))
    monkeypatch.setattr(ui, "_describe", lambda el: {})
    monkeypatch.setattr(ui, "_value", lambda el: "a+b")
    monkeypatch.setattr(ui.time, "sleep", lambda seconds: None)
    result = ui.type_text("test", None, {}, "a+b", tab_out=True)
    assert result["method"] == "keys"
    assert calls == ["click", "^a{BACKSPACE}", "a{+}b", "{TAB}"]
