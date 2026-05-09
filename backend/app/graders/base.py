from dataclasses import dataclass, field
from typing import Any, Literal


GraderStatus = Literal["ok", "error"]


@dataclass
class GraderResult:
    """Pure result of a grader run. The route layer persists this as a
    grader_runs row (append-only)."""

    status: GraderStatus
    score: int | None
    details: dict[str, Any] = field(default_factory=dict)
