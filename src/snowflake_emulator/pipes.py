"""
Snowpipe continuous ingestion manager for Snowflake Emulator.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class FileLoadStatus:
    path: str
    status: str  # "LOADED", "LOAD_FAILED"
    rows_loaded: int = 0
    errors_seen: int = 0
    first_error_message: Optional[str] = None
    time: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))


class PipeManager:
    def __init__(self):
        # pipe_name -> list of FileLoadStatus
        self.load_history: Dict[str, List[FileLoadStatus]] = {}

    def record_load(self, pipe_name: str, path: str, status: str, rows_loaded: int = 0, error: Optional[str] = None):
        clean_name = pipe_name.upper()
        if clean_name not in self.load_history:
            self.load_history[clean_name] = []
        
        load_record = FileLoadStatus(
            path=path,
            status=status,
            rows_loaded=rows_loaded,
            errors_seen=1 if error else 0,
            first_error_message=error
        )
        self.load_history[clean_name].append(load_record)
        return load_record

    def get_insert_report(self, pipe_name: str) -> Dict[str, Any]:
        clean_name = pipe_name.upper()
        records = self.load_history.get(clean_name, [])
        return {
            "pipe": clean_name,
            "completeResult": True,
            "files": [
                {
                    "path": r.path,
                    "stage": clean_name,
                    "status": r.status,
                    "rowsParsed": r.rows_loaded,
                    "rowsLoaded": r.rows_loaded,
                    "errorsSeen": r.errors_seen,
                    "firstError": r.first_error_message
                }
                for r in records[-50:]  # last 50
            ]
        }

    def get_load_history(self, pipe_name: str) -> Dict[str, Any]:
        clean_name = pipe_name.upper()
        records = self.load_history.get(clean_name, [])
        return {
            "pipe": clean_name,
            "completeResult": True,
            "files": [
                {
                    "path": r.path,
                    "status": r.status,
                    "rowsLoaded": r.rows_loaded,
                    "errorsSeen": r.errors_seen,
                    "lastModifiedTime": r.time
                }
                for r in records
            ]
        }
