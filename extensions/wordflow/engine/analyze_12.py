# -*- coding: utf-8 -*-
"""C-05 analyze_12 — offline analysis of text/docs into architecture seed. 0% LLM."""
from __future__ import annotations

import hashlib
import re
from typing import Any

_HEADING = re.compile(r"^(#{1,3})\s+(.+)$", re.M)
_CODE_FENCE = re.compile(r"```[a-zA-Z0-9_]*\n[\s\S]*?```", re.M)
_PATH_HINT = re.compile(
    r"(?:^|\s)([a-zA-Z0-9_./-]+\.(?:py|yaml|yml|json|md))(?:\s|$)",
)


class AnalyzeError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def analyze_document(text: str, *, doc_id: str = "doc") -> dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        raise AnalyzeError("EMPTY_DOCUMENT")

    headings = [{"level": len(m.group(1)), "title": m.group(2).strip()}
                for m in _HEADING.finditer(text)]
    fences = _CODE_FENCE.findall(text)
    paths = sorted(set(m.group(1) for m in _PATH_HINT.finditer(text)))

    components = []
    for i, h in enumerate(headings[:20]):
        components.append({
            "id": f"c{i:02d}",
            "role": "section",
            "title": h["title"],
            "level": h["level"],
        })

    files = [{"path": p, "kind": _kind(p), "description": "hint_from_doc"} for p in paths[:30]]
    if not files:
        files = [{"path": f"derived/{doc_id}.md", "kind": "md", "description": "source_doc"}]

    seed = {
        "schema_version": "1.0",
        "artifact_id": f"arch.{doc_id}",
        "summary": headings[0]["title"] if headings else doc_id,
        "components": components,
        "files": files,
        "evidence_ref": {
            "task_id": "C-05",
            "claim_status": "PARTIAL",
            "doc_anchors": [doc_id],
            "content_sha256": _content_hash(text),
            "code_fence_count": len(fences),
            "heading_count": len(headings),
        },
    }
    return {
        "ok": True,
        "track": "knowledge",
        "architecture_seed": seed,
        "metrics": {
            "headings": len(headings),
            "code_fences": len(fences),
            "path_hints": len(paths),
            "chars": len(text),
        },
        "llm_control": "DENY",
    }


def analyze_12(documents: list[dict[str, str]]) -> dict[str, Any]:
    """documents: [{id, text}, ...] → batch analyze."""
    if not documents:
        raise AnalyzeError("NO_DOCUMENTS")
    results = []
    for d in documents:
        if not isinstance(d, dict):
            raise AnalyzeError("DOC_NOT_OBJECT")
        rid = str(d.get("id") or d.get("doc_id") or "doc")
        text = str(d.get("text") or d.get("content") or "")
        results.append(analyze_document(text, doc_id=rid))
    return {
        "ok": True,
        "count": len(results),
        "results": results,
        "llm_control": "DENY",
    }


def _kind(path: str) -> str:
    if path.endswith(".py"):
        return "py"
    if path.endswith((".yaml", ".yml")):
        return "yaml"
    if path.endswith(".json"):
        return "json"
    if path.endswith(".md"):
        return "md"
    return "other"
