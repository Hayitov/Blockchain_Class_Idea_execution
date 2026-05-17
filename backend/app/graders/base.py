from dataclasses import dataclass, field
from typing import Any, Literal


GraderStatus = Literal["ok", "error"]


@dataclass
class GraderResult:
    status: GraderStatus
    score: int | None
    details: dict[str, Any] = field(default_factory=dict)
