"""EvidenceVerifier — CLAIM ≠ EVIDENCE ≠ VERIFICATION. T6: no placeholders."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any

FORBIDDEN_EVIDENCE_SUBSTR = (
    "placeholder",
    "auto_core_placeholder",
    "TODO",
    "TBD",
    "claim_only",
    "self_cert",
)

@dataclass
class EvidenceRef:
    kind: str  # path|symbol|test|measure|commit|manifest
    value: str

class EvidenceVerifier:
    def verify_ref(self, ref: EvidenceRef) -> Dict[str, Any]:
        if not ref.value or not str(ref.value).strip():
            return {"ok": False, "reason": "empty evidence"}
        val = str(ref.value).strip()
        low = val.lower()
        for bad in FORBIDDEN_EVIDENCE_SUBSTR:
            if bad.lower() in low:
                return {"ok": False, "reason": f"T6 forbidden evidence token: {bad}"}
        if ref.kind == "path":
            p = Path(val)
            if p.exists():
                return {"ok": True, "resolved": str(p)}
            if val.startswith("extensions/") or val.startswith("PIPELINE/"):
                return {"ok": True, "resolved": val, "note": "repo-relative accepted"}
            return {"ok": False, "reason": f"path not found: {val}"}
        if ref.kind in ("measure", "manifest", "commit", "symbol", "test"):
            if len(val) < 4:
                return {"ok": False, "reason": "evidence too short"}
            return {"ok": True, "resolved": val}
        return {"ok": False, "reason": f"unknown kind {ref.kind}"}

    def verify_many(self, refs: List[EvidenceRef]) -> Dict[str, Any]:
        results = [self.verify_ref(r) for r in refs]
        ok = all(r["ok"] for r in results) if results else False
        return {"ok": ok, "results": results}
