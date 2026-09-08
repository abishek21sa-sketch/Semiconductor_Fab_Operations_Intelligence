from __future__ import annotations
import csv, json
from pathlib import Path
from pydantic import ValidationError
from fabops.ingestion.events import FabEvent

class IngestionError(ValueError):
    pass

def load_jsonl(path: str | Path) -> list[FabEvent]:
    events=[]
    for lineno, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            events.append(FabEvent.model_validate(json.loads(line)))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise IngestionError(f"invalid event at line {lineno}: {exc}") from exc
    return events

def load_csv(path: str | Path) -> list[FabEvent]:
    events=[]
    with Path(path).open(newline="", encoding="utf-8") as f:
        for lineno, row in enumerate(csv.DictReader(f), 2):
            clean={k:v for k,v in row.items() if v not in (None,"")}
            for key in ("timestamp","step","quantity"):
                if key in clean:
                    clean[key] = float(clean[key]) if key=="timestamp" else int(clean[key])
            if "payload" in clean and isinstance(clean["payload"], str):
                clean["payload"] = json.loads(clean["payload"] or "{}")
            try:
                events.append(FabEvent.model_validate(clean))
            except (ValidationError, json.JSONDecodeError) as exc:
                raise IngestionError(f"invalid event at CSV row {lineno}: {exc}") from exc
    return events
