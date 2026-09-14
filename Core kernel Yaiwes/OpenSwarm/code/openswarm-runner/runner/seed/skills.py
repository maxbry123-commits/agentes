"""Lay the user's skills down where the backend looks for them, before it boots.

backend/apps/skills/skills.py hardwires SKILLS_DIR to ~/.claude/skills and gates the whole
Skill tool on at least one non-built-in skill existing there. A container that ships without
them does not get a degraded Skill tool, it gets no Skill tool at all, and the agent then
answers from general knowledge in a voice that sounds exactly as confident as the real thing.

Written pre-boot for the same reason the workflow is: the skill index is read once at startup.
"""

import logging
import os
from typing import List

from typeguard import typechecked

from runner.run_spec import SkillPayload

logger = logging.getLogger(__name__)

SKILLS_DIRNAME = os.path.join(".claude", "skills")


@typechecked
def skills_dir(home: str) -> str:
    return os.path.join(home, SKILLS_DIRNAME)


@typechecked
def write_skills(home: str, skills: List[SkillPayload]) -> int:
    """Write every skill folder. Returns how many landed.

    Paths were already proven relative and non-escaping by SkillFile's validator; this re-checks
    the joined result anyway, because the one place a path traversal is worth catching twice is
    the line that actually opens the file.
    """
    root = skills_dir(home)
    os.makedirs(root, mode=0o700, exist_ok=True)
    written = 0
    for skill in skills:
        folder = os.path.join(root, skill.id)
        for file in skill.files:
            target = os.path.abspath(os.path.join(folder, file.path))
            if not target.startswith(os.path.abspath(folder) + os.sep):
                raise ValueError(f"skill {skill.id!r} file {file.path!r} resolves outside its own folder")
            os.makedirs(os.path.dirname(target), mode=0o700, exist_ok=True)
            with open(target, "w", encoding="utf-8") as handle:
                handle.write(file.text)
        written += 1
    if written:
        logger.info("seeded %d skill(s) into %s", written, root)
    return written
