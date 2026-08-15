# -*- coding: utf-8 -*-
"""C-11 Native project document templates — Wordflow generates these. 0% LLM."""
from __future__ import annotations

from typing import Any

TEMPLATES: dict[str, str] = {
    "README.md": "# {project_name}\n\n{summary}\n\n## Status\n\n- mission_id: {mission_id}\n- llm_control: DENY\n",
    "PROJECT_PROFILE.md": "# PROJECT_PROFILE\n\nname: {project_name}\nmission_id: {mission_id}\nobjectives:\n{objectives_block}\n",
    "MASTER_PROJECT.md": "# MASTER_PROJECT\n\nPipeline memory for {project_name}.\nmission_id: {mission_id}\n",
    "ARCHITECTURE.md": "# ARCHITECTURE\n\n{project_name} architecture seed.\ncomponents: see architecture_output.\n",
    "WORKFLOW.md": "# WORKFLOW\n\nDeterministic stages for {project_name}.\nMAIN_12 → evidence → deploy.\n",
    "PIPELINE.md": "# PIPELINE\n\nBitácora / trazabilidad {project_name}.\nmission_id: {mission_id}\n",
    "CAPABILITIES.md": "# CAPABILITIES\n\nResource/Capability map for {project_name}.\n",
    "PLUGINS.md": "# PLUGINS\n\nExtension list (KER packages).\n",
    "CONNECTORS.md": "# CONNECTORS\n\nGitHub / HF / SSH adapters.\n",
    "EVOLUTION.md": "# EVOLUTION\n\nCross-task evolution log.\n",
    "TRACEABILITY.md": "# TRACEABILITY\n\nmission_id: {mission_id}\ndoc_anchors: C-11\n",
    "CHANGELOG.md": "# CHANGELOG\n\n## Unreleased\n\n- bootstrap docs for {project_name}\n",
}


class DocsTemplateError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def list_templates() -> list[str]:
    return sorted(TEMPLATES.keys())


def generate_project_docs(
    *,
    project_name: str,
    mission_id: str = "",
    summary: str = "",
    objectives: list[str] | None = None,
    only: list[str] | None = None,
) -> dict[str, Any]:
    if not project_name:
        raise DocsTemplateError("PROJECT_NAME_EMPTY")

    objs = objectives or []
    objectives_block = "\n".join(f"  - {o}" for o in objs) if objs else "  - TBD"
    ctx = {
        "project_name": project_name,
        "mission_id": mission_id or "pending",
        "summary": summary or f"Project {project_name}",
        "objectives_block": objectives_block,
    }

    names = only or list(TEMPLATES.keys())
    files: dict[str, str] = {}
    for name in names:
        if name not in TEMPLATES:
            raise DocsTemplateError("UNKNOWN_TEMPLATE", name)
        files[name] = TEMPLATES[name].format(**ctx)

    return {
        "ok": True,
        "project_name": project_name,
        "mission_id": ctx["mission_id"],
        "files": files,
        "count": len(files),
        "llm_control": "DENY",
    }
