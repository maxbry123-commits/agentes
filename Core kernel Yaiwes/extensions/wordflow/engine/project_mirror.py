# -*- coding: utf-8 -*-
"""C-16 project_mirror — isolated project contexts (no cross-talk). 0% LLM."""
from __future__ import annotations

import copy
from typing import Any

from extensions.wordflow.state.blackboard import Blackboard


class ProjectMirrorError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


class ProjectMirror:
    """Registry of isolated project runtimes (docs/repos/blackboard separate)."""

    def __init__(self) -> None:
        self._projects: dict[str, dict[str, Any]] = {}

    def create(
        self,
        project_id: str,
        *,
        mission_id: str = "",
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not project_id:
            raise ProjectMirrorError("PROJECT_ID_EMPTY")
        if project_id in self._projects:
            raise ProjectMirrorError("PROJECT_EXISTS", project_id)
        bb = Blackboard(mission_id=mission_id or project_id)
        self._projects[project_id] = {
            "project_id": project_id,
            "mission_id": mission_id or project_id,
            "blackboard": bb,
            "meta": dict(meta or {}),
            "docs": {},
            "resources": {},
            "llm_control": "DENY",
        }
        return {"ok": True, "project_id": project_id}

    def get(self, project_id: str) -> dict[str, Any]:
        p = self._projects.get(project_id)
        if not p:
            raise ProjectMirrorError("PROJECT_NOT_FOUND", project_id)
        return p

    def set_doc(self, project_id: str, name: str, content: str) -> None:
        p = self.get(project_id)
        p["docs"][name] = content

    def set_resource(self, project_id: str, resource_id: str, data: dict[str, Any]) -> None:
        p = self.get(project_id)
        p["resources"][resource_id] = dict(data)

    def snapshot(self, project_id: str) -> dict[str, Any]:
        p = self.get(project_id)
        return {
            "project_id": p["project_id"],
            "mission_id": p["mission_id"],
            "meta": copy.deepcopy(p["meta"]),
            "docs": dict(p["docs"]),
            "resources": copy.deepcopy(p["resources"]),
            "blackboard": p["blackboard"].snapshot(),
            "llm_control": "DENY",
        }

    def list_projects(self) -> list[str]:
        return sorted(self._projects.keys())

    def mirror(self, source_id: str, new_id: str) -> dict[str, Any]:
        """Clone isolation boundary (deep copy docs/meta; fresh blackboard)."""
        src = self.get(source_id)
        if new_id in self._projects:
            raise ProjectMirrorError("PROJECT_EXISTS", new_id)
        self.create(new_id, mission_id=src["mission_id"], meta=src["meta"])
        dest = self.get(new_id)
        dest["docs"] = dict(src["docs"])
        dest["resources"] = copy.deepcopy(src["resources"])
        return {"ok": True, "source": source_id, "mirror": new_id}
