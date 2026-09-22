"""Versioned JSON reports. A parsed report alone does not certify process exit."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

VERSION = 1


def load_object(path: str | Path) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    data = json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=unique)
    if not isinstance(data, dict):
        raise ValueError("expected a JSON object")
    return data


def string(data: dict[str, Any], key: str, *, empty: bool = False) -> str:
    value = data.get(key)
    if not isinstance(value, str) or (not empty and not value):
        raise ValueError(f"{key} must be {'a' if empty else 'a nonempty'} string")
    return value


def integer(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if type(value) is not int or value < 0:
        raise ValueError(f"{key} must be a nonnegative integer")
    return value


def report(
    path: str | Path, request_id: str | None = None, application: str | None = None
) -> dict[str, Any]:
    data = load_object(path)
    if integer(data, "schema_version") != VERSION:
        raise ValueError("unsupported report schema_version")
    identity = string(data, "request_id")
    app = string(data, "application")
    if request_id is not None and identity != request_id:
        raise ValueError("report request_id mismatch")
    if application is not None and app != application:
        raise ValueError("report application mismatch")
    if data.get("completed") is not True:
        raise ValueError("report is not complete")
    string(data, "requested_suite", empty=True)
    string(data, "suite", empty=True)
    cases = data.get("cases")
    if not isinstance(cases, list):
        raise ValueError("cases must be an array")
    counts = {"pass": 0, "fail": 0, "error": 0}
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("case must be an object")
        for key in ("suite", "classname", "name"):
            string(case, key)
        string(case, "message", empty=True)
        status = string(case, "status")
        if status not in counts:
            raise ValueError(f"unknown case status: {status}")
        counts[status] += 1
        elapsed = case.get("time")
        if isinstance(elapsed, bool) or not isinstance(elapsed, (int, float)):
            raise ValueError("case time must be a finite nonnegative number")
        if not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError("case time must be a finite nonnegative number")
    for key, actual in (
        ("tests", len(cases)),
        ("passed", counts["pass"]),
        ("failures", counts["fail"]),
        ("errors", counts["error"]),
    ):
        if integer(data, key) != actual:
            raise ValueError(f"inconsistent {key} count")
    runner_errors = data.get("runner_errors")
    if not isinstance(runner_errors, list) or any(not isinstance(x, str) for x in runner_errors):
        raise ValueError("runner_errors must be an array of strings")
    data["ok"] = bool(cases) and not (counts["fail"] or counts["error"] or runner_errors)
    data["summary"] = (
        f"{data['suite']}: {len(cases)} tests, {counts['pass']} passed, "
        f"{counts['fail']} failed, {counts['error']} errors"
    )
    details = [
        f"{c['status'].upper()} {c['classname']}.{c['name']}: {c['message']}"
        for c in cases
        if c["status"] != "pass"
    ]
    data["summary"] += "".join(f"\n{x}" for x in [*details, *runner_errors])
    return data
