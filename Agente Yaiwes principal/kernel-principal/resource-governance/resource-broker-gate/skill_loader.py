"""SkillLoader — SKILL.md → Skill IR / ResourceContract (never execute markdown)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .contract import ResourceContract


@dataclass
class SkillIR:
    name: str
    description: str = ""
    capabilities: tuple[str, ...] = ()
    procedures: tuple[str, ...] = ()
    raw_headings: tuple[str, ...] = ()
    source_path: str | None = None


class SkillLoader:
    def load_text(self, text: str, source_path: str | None = None) -> SkillIR:
        lines = text.splitlines()
        name = "skill"
        description = ""
        headings = []
        procedures = []
        for i, line in enumerate(lines):
            if line.startswith("# "):
                name = line[2:].strip() or name
                if i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                    description = lines[i + 1].strip()
            elif line.startswith("## "):
                h = line[3:].strip()
                headings.append(h)
                procedures.append(h)
            elif re.match(r"^[-*]\s+", line.strip()):
                procedures.append(line.strip().lstrip("-* "))
        caps = tuple(
            p.lower().replace(" ", "_")[:64]
            for p in headings[:12]
        ) or ("skill.execute",)
        return SkillIR(
            name=name,
            description=description,
            capabilities=caps,
            procedures=tuple(procedures[:50]),
            raw_headings=tuple(headings),
            source_path=source_path,
        )

    def load_file(self, path: str | Path) -> SkillIR:
        p = Path(path)
        return self.load_text(p.read_text(encoding="utf-8"), source_path=str(p))

    def to_contract(self, ir: SkillIR, resource_id: str | None = None) -> ResourceContract:
        rid = resource_id or f"skill://{ir.name.lower().replace(' ', '_')}"
        return ResourceContract(
            resource_id=rid,
            provider="local",
            kind="skill",
            source_uri=ir.source_path or rid,
            capabilities=ir.capabilities,
            transport="local",
            entrypoint=ir.name,
            acquisition_mode="file",
            trusted=False,
        )
