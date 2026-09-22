from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def write_report() -> Callable[..., dict[str, Any]]:
    def write(
        out: Path,
        request_id: str = "abc123",
        application: str = "sample",
        statuses: tuple[str, ...] = ("pass",),
        suite: str = "n_suite_all",
        requested_suite: str = "",
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "schema_version": 1,
            "request_id": request_id,
            "application": application,
            "requested_suite": requested_suite,
            "suite": suite,
            "completed": True,
            "tests": len(statuses),
            "passed": statuses.count("pass"),
            "failures": statuses.count("fail"),
            "errors": statuses.count("error"),
            "runner_errors": [],
            "cases": [
                {
                    "suite": suite,
                    "classname": "n_test_sample",
                    "name": f"test_{i}",
                    "status": status,
                    "message": 'quote " and slash \\ and newline\n\tΩ' if status != "pass" else "",
                    "time": 0.125,
                }
                for i, status in enumerate(statuses)
            ],
        }
        out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8-sig")
        return data

    return write
