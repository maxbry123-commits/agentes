from __future__ import annotations
from dataclasses import dataclass, field
from schemas.base import new_id


@dataclass(slots=True)
class AutoDebugRecord:
    record_id: str = field(default_factory=lambda: new_id("debug"))
    experiment_id: str = ""
    result_id: str = ""
    patch_id: str = ""
    attempt_number: int = 0
    error_summary: str = ""
    fix_description: str = ""
    fix_file_contents: dict[str, str] = field(default_factory=dict)
    fix_successful: bool = False
    llm_call_id: str = ""
    log_artifact_id: str = ""
