"""Shared in-memory job state for the ingestion pipeline."""
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class JobState:
    status: str = "idle"   # idle | running | done | error
    files_total: int = 0
    files_done: int = 0
    current_file: str = ""
    message: str = ""
    error: str = ""
    timings: dict = field(default_factory=dict)  # {filename: {phase: seconds}}

    @property
    def pct(self) -> int:
        if self.files_total == 0:
            return 0
        return round(self.files_done / self.files_total * 100)


job = JobState()
lock = Lock()

scrape_job = JobState()
scrape_lock = Lock()
