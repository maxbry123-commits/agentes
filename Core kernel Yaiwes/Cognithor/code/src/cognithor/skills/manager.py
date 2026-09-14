"""Management for external skills (procedures).

Skills are defined as Markdown files with frontmatter and stored in the
``skills`` directory within the Cognithor home. This manager provides
functions for listing existing skills and creating new templates.
Automatic installation from remote sources can be added later.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def list_skills(skills_dir: Path) -> list[str]:
    """List all available skills.

    Args:
        skills_dir: Directory where skill files are located.

    Returns:
        List of skill file names (without path).
    """
    if not skills_dir.exists():
        return []
    return [p.name for p in skills_dir.glob("*.md") if p.is_file()]


def _slugify(name: str) -> str:
    """Create a filename slug from an arbitrary name.

    Converts to lowercase, replaces spaces with hyphens,
    and removes all characters except letters, numbers, and hyphens.
    """
    slug = name.lower().strip()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    return slug


def create_skill(
    skills_dir: Path, name: str, trigger_keywords: Iterable[str] | None = None
) -> Path:
    """Create a new skill file with a minimal template.

    Args:
        skills_dir: Storage location for skills.
        name: Display name of the new skill. Used in the frontmatter title
            and slugified as the filename.
        trigger_keywords: Keywords that trigger this skill.

    Returns:
        Path to the newly created skill file.
    """
    if trigger_keywords is None:
        trigger_keywords = []
    slug = _slugify(name)
    filename = f"{slug}.md"
    path = skills_dir / filename
    if path.exists():
        raise FileExistsError(f"Skill '{name}' existiert bereits: {path}")
    # Frontmatter for a procedure
    triggers = ", ".join(trigger_keywords)
    content = (
        "---\n"
        f"name: {name}\n"
        f"trigger_keywords: [{triggers}]\n"
        "---\n"
        "# " + name + "\n\n"
        "## Voraussetzungen\n\n"
        "Beschreibe hier die Voraussetzungen für diesen Skill.\n\n"
        "## Schritte\n\n"
        "1. Detaillierte Schritt-für-Schritt-Anleitung.\n\n"
        "## Hinweise\n\n"
        "Notiere bekannte Fehlerfälle oder Tipps.\n"
    )
    skills_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def search_remote_skills(query: str, limit: int = 10) -> list[str]:
    """Search local "remote" skill repos for matching skills.

    In the absence of a real marketplace, this function searches the
    provided example procedures in the repository to simulate a remote
    search. Both file names and their frontmatter content are examined.
    The result is a list of skill file names (without extension),
    sorted by simple match.

    Args:
        query: Search term for skills (case-insensitive).
        limit: Maximum number of results.

    Returns:
        List of skill base names (without ``.md``) matching the query.
    """
    query_lower = query.lower().strip()
    results: list[str] = []

    # Determine potential "remote" directories relative to this module
    here = Path(__file__).resolve()
    # Structure: project/src/jarvis/skills/manager.py → parents[4] = project
    # We consider two locations as sources for "remote" skills:
    #  1. <repo_root>/project/data/procedures
    #  2. <repo_root>/data/procedures
    # parents[4] -> <repo_root>/project, parents[5] -> <repo_root>
    project_dir = here.parents[4]
    repo_root = here.parents[5]
    candidate_dirs = [
        project_dir / "data" / "procedures",
        repo_root / "data" / "procedures",
    ]

    seen: set[str] = set()
    for directory in candidate_dirs:
        if not directory.exists():
            continue
        for file_path in directory.glob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception:
                continue
            name = file_path.stem
            # Examine frontmatter (first ~20 lines) for name and trigger_keywords
            fm_name: str | None = None
            fm_triggers: list[str] = []
            try:
                lines = content.splitlines()
                for line in lines[:20]:
                    # Name line
                    if line.lower().startswith("name:"):
                        fm_name = line.split("name:", 1)[1].strip()
                    elif line.lower().startswith("trigger_keywords"):
                        # Extract list between square brackets
                        after = line.split("[", 1)
                        if len(after) > 1:
                            inside = after[1].split("]", 1)[0]
                            # Split by commas
                            for kw in inside.split(","):
                                kw = kw.strip().strip("'\"")
                                if kw:
                                    fm_triggers.append(kw)
                    # Stop when frontmatter ends (first section after "---")
                    if line.strip() == "---":
                        break
            except Exception:
                pass  # Cleanup — frontmatter parsing failure is non-critical

            # Check if query appears in filename, frontmatter name, triggers, or content
            match_found = False
            if (
                query_lower in name.lower()
                or (fm_name and query_lower in fm_name.lower())
                or any(query_lower in kw.lower() for kw in fm_triggers)
                or query_lower in content.lower()
            ):
                match_found = True

            if match_found and name not in seen:
                results.append(name)
                seen.add(name)
                if len(results) >= limit:
                    return results
    return results


def install_remote_skill(skills_dir: Path, name: str, repo_url: str | None = None) -> Path:
    """Install a skill from a local "remote" repository.

    This function attempts to copy an existing procedure (skill) from the
    example procedures in the repository and place it under the
    given name in the plugins directory. If the skill is already
    installed, the existing path is returned. If no matching skill
    is found, an empty template is created.

    Args:
        skills_dir: Target directory for the skill.
        name: Name of the skill to install. Can be either the
            filename without extension or the visible frontmatter name.
        repo_url: Optional reference to a remote repository (ignored
            in this offline variant).

    Returns:
        Path to the installed or created skill file.
    """
    # Normalize the filename
    slug = _slugify(name)
    target_filename = f"{slug}.md"
    target_path = skills_dir / target_filename

    # If already installed, return the path
    if target_path.exists():
        return target_path

    # Determine "remote" source directories
    here = Path(__file__).resolve()
    # parents[4] -> <repo_root>/project, parents[5] -> <repo_root>
    project_dir = here.parents[4]
    repo_root = here.parents[5]
    source_dirs = [
        project_dir / "data" / "procedures",
        repo_root / "data" / "procedures",
    ]

    # Search for a matching source file
    source_file: Path | None = None
    for directory in source_dirs:
        if not directory.exists():
            continue
        for file_path in directory.glob("*.md"):
            if file_path.stem.lower() == slug:
                source_file = file_path
                break
        if source_file:
            break

    # If found, copy the content to the target
    if source_file is not None and source_file.exists():
        try:
            content = source_file.read_text(encoding="utf-8")
        except Exception:
            content = ""
        skills_dir.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        return target_path

    # Otherwise create an empty template as before
    content = (
        f"name: {name}\n"
        f"trigger_keywords: []\n"
        "---\n"
        f"# {name}\n\n"
        "## Beschreibung\n\n"
        "Dieser Skill wurde automatisch erstellt. Er muss manuell mit Inhalt befüllt werden.\n"
    )
    skills_dir.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content, encoding="utf-8")
    return target_path
