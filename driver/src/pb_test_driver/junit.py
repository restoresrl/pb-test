"""Offline reader for legacy v0.1 JUnit reports; not used by JSON execution."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Case:
    suite: str
    classname: str
    name: str
    status: str  # pass | fail | error
    message: str
    time: float


@dataclass
class Results:
    name: str
    tests: int
    failures: int
    errors: int
    time: float
    cases: list[Case] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return self.tests - self.failures - self.errors

    @property
    def ok(self) -> bool:
        return self.failures == 0 and self.errors == 0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["passed"] = self.passed
        data["ok"] = self.ok
        return data

    def summary(self) -> str:
        head = (
            f"{self.name}: {self.tests} tests, {self.passed} passed, "
            f"{self.failures} failed, {self.errors} errors"
        )
        lines = [head]
        for case in self.cases:
            if case.status != "pass":
                lines.append(f"{case.status.upper()} {case.classname}.{case.name}: {case.message}")
        return "\n".join(lines)


def _float(value: str | None) -> float:
    try:
        return float(value or "0")
    except ValueError:
        return 0.0


def parse_text(text: str) -> Results:
    root = ET.fromstring(text.lstrip("\ufeff"))
    if root.tag == "testsuites":
        suites = list(root.iter("testsuite"))
        name = root.get("name") or ""
    elif root.tag == "testsuite":
        suites = [root]
        name = root.get("name") or ""
    else:
        raise ValueError(f"not a JUnit document: root element is <{root.tag}>")
    cases: list[Case] = []
    for suite in suites:
        suite_name = suite.get("name") or name
        for tc in suite.iter("testcase"):
            failure = tc.find("failure")
            error = tc.find("error")
            # element text keeps line breaks; the attribute has them normalised to spaces
            if error is not None:
                status, message = "error", (error.text or "").strip() or error.get("message") or ""
            elif failure is not None:
                status = "fail"
                message = (failure.text or "").strip() or failure.get("message") or ""
            else:
                status, message = "pass", ""
            cases.append(
                Case(
                    suite=suite_name,
                    classname=tc.get("classname") or "",
                    name=tc.get("name") or "",
                    status=status,
                    message=message,
                    time=_float(tc.get("time")),
                )
            )
    return Results(
        name=name,
        tests=len(cases),
        failures=sum(1 for c in cases if c.status == "fail"),
        errors=sum(1 for c in cases if c.status == "error"),
        time=_float(root.get("time")),
        cases=cases,
    )


def parse_file(path: str | Path) -> Results:
    return parse_text(Path(path).read_text(encoding="utf-8-sig"))
