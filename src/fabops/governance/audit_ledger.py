"""Append-only tamper-evident governance ledger for fab decision evidence.

The ledger is deliberately small and local: it proves provenance/integrity for the
portfolio workstation without claiming to be a regulated MES/eDHR system. Each line
is chained to the previous entry and can be verified independently after export.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

GENESIS = "0" * 64


def _canonical(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _entry_hash(core: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(core)).hexdigest()


def read_ledger(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON at ledger line {lineno}") from exc
        rows.append(obj)
    return rows


def append_entry(
    path: str | Path,
    *,
    event_type: str,
    payload: dict[str, Any],
    actor: str = "PORTFOLIO_OPERATOR",
    approval_authority: str = "FAB_SHIFT_SUPERVISOR",
) -> dict[str, Any]:
    if not event_type.strip():
        raise ValueError("event_type is required")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = read_ledger(p)
    prev = rows[-1].get("entry_sha256", GENESIS) if rows else GENESIS
    sequence = len(rows) + 1
    core = {
        "sequence": sequence,
        "event_type": event_type,
        "actor": actor,
        "approval_authority": approval_authority,
        "previous_sha256": prev,
        "payload": payload,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    entry = {**core, "entry_sha256": _entry_hash(core)}
    with p.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(entry, sort_keys=True, separators=(",", ":"), default=str) + "\n")
        f.flush()
    return entry


def verify_ledger(path: str | Path) -> dict[str, Any]:
    try:
        rows = read_ledger(path)
    except ValueError as exc:
        return {"valid": False, "entries": 0, "first_invalid_sequence": None, "reason": str(exc)}
    previous = GENESIS
    for idx, entry in enumerate(rows, 1):
        stored = entry.get("entry_sha256")
        core = {k: v for k, v in entry.items() if k != "entry_sha256"}
        if entry.get("sequence") != idx:
            return {"valid": False, "entries": len(rows), "first_invalid_sequence": idx, "reason": "sequence mismatch"}
        if entry.get("previous_sha256") != previous:
            return {"valid": False, "entries": len(rows), "first_invalid_sequence": idx, "reason": "chain mismatch"}
        if stored != _entry_hash(core):
            return {"valid": False, "entries": len(rows), "first_invalid_sequence": idx, "reason": "entry hash mismatch"}
        previous = str(stored)
    return {
        "valid": True,
        "entries": len(rows),
        "first_invalid_sequence": None,
        "head_sha256": previous,
        "ledger_type": "FABOPS_HASH_CHAIN_V1",
    }
