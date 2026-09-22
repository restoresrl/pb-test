"""File requests shared by user-started IDE runs and driver-started executables.

Receipts live with the evidence, not in process memory. A lock directory reserves
one application/start-directory slot until cleanup; it is never stolen on timeout.
"""

from __future__ import annotations

import json
import math
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

from pb_test_driver import protocol

NAME = re.compile(r"^[a-z_][a-z0-9_]*$")


def _publish(path: Path, data: dict[str, Any]) -> None:
    """Publish a complete file without replacing an existing destination."""
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        # Windows rename refuses an existing destination. Hard-link publication
        # supplies the same no-clobber property on POSIX test hosts.
        if os.name == "nt":
            temporary.rename(path)
        else:
            os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def prepare(
    application: str,
    work_dir: str | Path,
    out: str | Path,
    suite: str = "",
    ttl: int = 1800,
) -> dict[str, Any]:
    application = application.lower()
    suite = suite.lower()
    if not NAME.fullmatch(application) or (suite and not NAME.fullmatch(suite)):
        raise ValueError("application and suite must be PowerBuilder class names")
    if type(ttl) is not int or not 1 <= ttl <= 86400:
        raise ValueError("ttl must be between 1 and 86400 seconds")
    directory = Path(work_dir).resolve()
    if not directory.is_dir():
        raise FileNotFoundError(f"startup directory not found: {directory}")
    output = Path(out).resolve()
    request_path = directory / f"{application}_test.json"
    active = Path(str(request_path) + ".active")
    lock = Path(str(request_path) + ".lock")
    receipt = output.with_name(output.name + ".request.json")
    diagnostic = Path(str(active) + ".error.json")
    reserved = (request_path, active, lock, diagnostic, Path(str(diagnostic) + ".tmp"))
    if any(output == p or output.is_relative_to(p) for p in reserved):
        raise ValueError("output must be outside the request's control paths")
    if output.exists() or receipt.exists():
        raise FileExistsError("use a fresh output and receipt path")
    lock.mkdir()  # Exclusive reservation, retained until explicit cleanup.
    try:
        if any(p.exists() for p in (request_path, active, Path(str(active) + ".error.json"))):
            raise FileExistsError(f"pending, active or rejected request at {request_path}")
        output.parent.mkdir(parents=True, exist_ok=True)
        request = {
            "schema_version": protocol.VERSION,
            "request_id": uuid.uuid4().hex,
            "application": application,
            "suite": suite,
            "output": str(output),
            "expires_at": int(time.time()) + ttl,
        }
        ticket = {"request_path": str(request_path), "request": request}
        _publish(lock / "owner.json", {"request_id": request["request_id"]})
        _publish(receipt, ticket)
        _publish(request_path, request)
    except BaseException:
        (lock / "owner.json").unlink(missing_ok=True)
        lock.rmdir()
        raise
    return {"receipt": str(receipt), **ticket}


def _ticket(receipt: str | Path) -> tuple[Path, dict[str, Any]]:
    ticket = protocol.load_object(receipt)
    path = Path(protocol.string(ticket, "request_path"))
    request = ticket.get("request")
    if not isinstance(request, dict):
        raise ValueError("invalid receipt request")
    for key in ("request_id", "application", "output"):
        protocol.string(request, key)
    if protocol.integer(request, "schema_version") != protocol.VERSION:
        raise ValueError("unsupported request schema_version")
    protocol.integer(request, "expires_at")
    protocol.string(request, "suite", empty=True)
    if not Path(request["output"]).is_absolute():
        raise ValueError("receipt output must be absolute")
    if not path.is_absolute() or path.name != f"{request['application']}_test.json":
        raise ValueError("invalid receipt request_path")
    return path, request


def status(receipt: str | Path) -> dict[str, Any]:
    path, request = _ticket(receipt)
    base = {"request_id": request["request_id"], "application": request["application"]}
    output = Path(request["output"])
    if output.exists():
        try:
            result = protocol.report(output, request["request_id"], request["application"])
            if result["requested_suite"] != request["suite"]:
                raise ValueError("report requested_suite mismatch")
            if request["suite"] and result["suite"] != request["suite"]:
                raise ValueError("report executed suite mismatch")
        except (ValueError, OSError) as exc:
            return {**base, "state": "invalid", "error": str(exc)}
        return {**base, "state": "completed", "results": result}
    active = Path(str(path) + ".active")
    # Recheck active after pending: PB can rename between the first two reads.
    for candidate, state in ((active, "active"), (path, "pending"), (active, "active")):
        try:
            current = protocol.load_object(candidate)
        except FileNotFoundError:
            continue
        except (ValueError, OSError) as exc:
            return {**base, "state": "invalid", "error": str(exc)}
        if current != request:
            return {**base, "state": "conflict", "error": "request content changed"}
        diagnostic = Path(str(path) + ".active.error.json")
        if diagnostic.exists():
            try:
                error = protocol.string(protocol.load_object(diagnostic), "error")
            except (ValueError, OSError) as exc:
                error = f"invalid rejection diagnostic: {exc}"
            return {**base, "state": "rejected", "error": error}
        if state == "pending" and time.time() >= request["expires_at"]:
            state = "expired"
        return {**base, "state": state}
    return {**base, "state": "missing"}


def wait(receipt: str | Path, timeout: float = 60.0, poll: float = 0.25) -> dict[str, Any]:
    if not math.isfinite(timeout) or timeout < 0:
        raise ValueError("timeout must be finite and nonnegative")
    deadline = time.monotonic() + timeout
    while True:
        result = status(receipt)
        if result["state"] not in ("pending", "active"):
            return {**result, "timed_out": False}
        if time.monotonic() >= deadline:
            return {**result, "timed_out": True}
        time.sleep(poll)


def cleanup(receipt: str | Path) -> dict[str, Any]:
    """Cancel a pending request or release a completed slot. Never stop an IDE run."""
    path, request = _ticket(receipt)
    state = status(receipt)
    if state["state"] not in ("pending", "expired", "completed"):
        raise ValueError(f"cannot clean up {state['state']} request; inspect it manually")
    active = Path(str(path) + ".active")
    lock = Path(str(path) + ".lock")
    owner = protocol.load_object(lock / "owner.json")
    if owner != {"request_id": request["request_id"]}:
        raise ValueError("refusing to release another request's reservation")
    if state["state"] == "completed":
        # Keep the report and receipt. Only remove control files with identical
        # contents; this also prevents cleanup of a later request at this slot.
        for candidate in (active, path):
            if candidate.exists() and protocol.load_object(candidate) != request:
                raise ValueError("refusing to remove another request")
        # A second launch may have diagnosed the already-active slot. Once the
        # original request is complete, archive that diagnostic with its receipt.
        diagnostic = Path(str(active) + ".error.json")
        if diagnostic.exists():
            archived = Path(receipt).with_name(Path(receipt).name + ".error.json")
            data = protocol.load_object(diagnostic)
            if archived.exists():
                if protocol.load_object(archived) != data:
                    raise ValueError("refusing to overwrite an archived diagnostic")
            else:
                _publish(archived, data)
            diagnostic.unlink()
        for candidate in (active, path):
            candidate.unlink(missing_ok=True)
    else:
        # Compete with PB's pending -> active rename. Only one rename wins.
        cancelled = path.with_name(path.name + ".cancelled." + request["request_id"])
        path.rename(cancelled)
        if protocol.load_object(cancelled) != request:
            raise ValueError(f"changed request retained at {cancelled}")
        cancelled.unlink()
    (lock / "owner.json").unlink()
    lock.rmdir()
    return {"request_id": request["request_id"], "state": "released"}
