# -*- coding: utf-8 -*-
"""C-06 skill_native_compiler — Skill/IR package → code_output seed. 0% LLM."""
from __future__ import annotations

from typing import Any

from extensions.wordflow.engine.dual_compiler import DualCompilerError, compile_output, promote_12


class SkillNativeError(Exception):
    def __init__(self, reason_code: str, detail: str = ""):
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}" if detail else reason_code)


def compile_skill_to_code(
    skill: dict[str, Any],
    *,
    module_path: str | None = None,
) -> dict[str, Any]:
    if not isinstance(skill, dict):
        raise SkillNativeError("SKILL_NOT_OBJECT")

    sid = skill.get("package_id") or skill.get("skill_id") or skill.get("id")
    if not sid:
        raise SkillNativeError("SKILL_ID_MISSING")

    version = str(skill.get("version") or "1.0.0")
    path = module_path or f"extensions/skills_native/{sid.replace('.', '/')}.py"

    body_lines = [
        f'# auto-generated from skill {sid}@{version}',
        '"""Native skill module — deterministic shell."""',
        "from __future__ import annotations",
        "",
        f"SKILL_ID = {sid!r}",
        f"SKILL_VERSION = {version!r}",
        f"INPUTS = {list(skill.get('inputs') or [])!r}",
        f"OUTPUTS = {list(skill.get('outputs') or [])!r}",
        "",
        "def run(payload: dict) -> dict:",
        "    return {",
        "        'ok': True,",
        f"        'skill_id': {sid!r},",
        "        'payload_keys': sorted(payload.keys()),",
        "        'llm_control': 'DENY',",
        "    }",
        "",
    ]
    content = "\n".join(body_lines)

    code_output = {
        "schema_version": "1.0",
        "artifact_id": f"skill_native.{sid}",
        "language": "python",
        "files": [{
            "path": path,
            "action": "create",
            "loc": content.count("\n") + 1,
        }],
        "evidence_ref": {
            "task_id": "C-06",
            "claim_status": "PARTIAL",
            "doc_anchors": [str(sid)],
        },
        "llm_control": "DENY",
    }

    validated = compile_output("code", code_output)
    return {
        "ok": True,
        "skill_id": sid,
        "version": version,
        "code_output": code_output,
        "content_map": {path: content},
        "validation": validated,
        "llm_control": "DENY",
    }


def compile_and_promote_skill(
    skill: dict[str, Any],
    *,
    version_pin: str,
    license: str = "MIT",
) -> dict[str, Any]:
    compiled = compile_skill_to_code(skill)
    promo = promote_12(
        package_id=str(compiled["skill_id"]),
        track="code",
        version_pin=version_pin,
        license=license,
        evidence_ref=compiled["code_output"].get("evidence_ref"),
    )
    return {
        "ok": bool(compiled.get("ok") and promo.get("ok")),
        "compiled": compiled,
        "promote": promo,
        "llm_control": "DENY",
    }
