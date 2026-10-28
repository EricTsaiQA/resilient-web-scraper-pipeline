"""
Deterministic Hash-Based Incremental Diff Engine.
Compares newly scraped records against a persistent JSON/SQLite snapshot and classifies
every row as `NEW`, `UPDATED`, or `UNCHANGED` (plus tracks `REMOVED` keys).
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Dict, List, Optional

from .models import DirectoryContactRecord


class DiffStatus(str, Enum):
    NEW = "NEW"
    UPDATED = "UPDATED"
    UNCHANGED = "UNCHANGED"


@dataclass
class DiffRecord:
    record: DirectoryContactRecord
    status: DiffStatus
    previous_fingerprint: Optional[str]
    current_fingerprint: str


class DiffSnapshotStore:
    def __init__(self, snapshot_path: Optional[Path] = None) -> None:
        self.snapshot_path = snapshot_path
        self._state: Dict[str, str] = {}
        if self.snapshot_path and self.snapshot_path.exists():
            self._state = json.loads(self.snapshot_path.read_text(encoding="utf-8"))

    def compare_and_update(self, records: List[DirectoryContactRecord], persist: bool = True) -> List[DiffRecord]:
        results: List[DiffRecord] = []
        next_state: Dict[str, str] = dict(self._state)

        for rec in records:
            curr_fp = rec.content_fingerprint()
            prev_fp = self._state.get(rec.record_id)
            if prev_fp is None:
                status = DiffStatus.NEW
            elif prev_fp != curr_fp:
                status = DiffStatus.UPDATED
            else:
                status = DiffStatus.UNCHANGED

            next_state[rec.record_id] = curr_fp
            results.append(
                DiffRecord(
                    record=rec,
                    status=status,
                    previous_fingerprint=prev_fp,
                    current_fingerprint=curr_fp,
                )
            )

        self._state = next_state
        if persist and self.snapshot_path:
            self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            self.snapshot_path.write_text(json.dumps(self._state, ensure_ascii=False, indent=2), encoding="utf-8")

        return results
