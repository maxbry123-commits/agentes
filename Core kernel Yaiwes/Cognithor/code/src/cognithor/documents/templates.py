"""Document template system for Typst-based document generation.

Templates are stored as .typ files in ~/.cognithor/templates/documents/.
Each template has a frontmatter comment block at the top and uses
{{variable}} placeholders that the LLM fills in before compilation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cognithor.utils.logging import get_logger

log = get_logger(__name__)

# Regex to find {{variable}} placeholders in Typst source
_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")

# Frontmatter field patterns
_FRONTMATTER_FIELDS = {
    "template": re.compile(r"^//\s*template:\s*(.+)$", re.MULTILINE),
    "description": re.compile(r"^//\s*description:\s*(.+)$", re.MULTILINE),
    "category": re.compile(r"^//\s*category:\s*(.+)$", re.MULTILINE),
    "variables": re.compile(r"^//\s*variables:\s*(.+)$", re.MULTILINE),
}


@dataclass
class DocumentTemplate:
    """Metadata and source reference for a single document template."""

    name: str
    slug: str
    description: str
    file_path: Path
    variables: list[str]
    category: str = "general"

    def __post_init__(self) -> None:
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for v in self.variables:
            if v not in seen:
                seen.add(v)
                unique.append(v)
        self.variables = unique


class TemplateManager:
    """Manages Typst document templates stored on disk.

    Templates live in ``~/.cognithor/templates/documents/`` as ``.typ`` files
    with a frontmatter comment block at the top.

    Usage::

        tm = TemplateManager()
        rendered = tm.render_template("brief", {"empfaenger_name": "Firma GmbH", ...})
        # Pass rendered source to MediaPipeline.typst_render()
    """

    def __init__(self, templates_dir: Path | None = None) -> None:
        self._templates_dir = (
            templates_dir or Path.home() / ".cognithor" / "templates" / "documents"
        )
        self._templates: dict[str, DocumentTemplate] = {}
        self._load_templates()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_templates(self) -> None:
        """Scan templates_dir for .typ files and parse their metadata."""
        self._templates.clear()

        if not self._templates_dir.exists():
            log.warning("templates_dir_missing", path=str(self._templates_dir))
            return

        for typ_file in sorted(self._templates_dir.glob("*.typ")):
            try:
                template = self._parse_template_file(typ_file)
                self._templates[template.slug] = template
                log.debug(
                    "template_loaded",
                    slug=template.slug,
                    variables=template.variables,
                )
            except Exception as exc:
                log.warning("template_parse_failed", file=str(typ_file), error=str(exc))

        log.info("templates_loaded", count=len(self._templates))

    def _parse_template_file(self, path: Path) -> DocumentTemplate:
        """Parse a .typ file and extract its metadata."""
        source = path.read_text(encoding="utf-8")

        # Extract frontmatter fields
        name_match = _FRONTMATTER_FIELDS["template"].search(source)
        desc_match = _FRONTMATTER_FIELDS["description"].search(source)
        cat_match = _FRONTMATTER_FIELDS["category"].search(source)
        vars_match = _FRONTMATTER_FIELDS["variables"].search(source)

        name = name_match.group(1).strip() if name_match else path.stem
        description = desc_match.group(1).strip() if desc_match else ""
        category = cat_match.group(1).strip() if cat_match else "general"

        # Variables from frontmatter comment
        frontmatter_vars: list[str] = []
        if vars_match:
            frontmatter_vars = [v.strip() for v in vars_match.group(1).split(",") if v.strip()]

        # Variables from {{placeholder}} patterns in source body
        body_vars = _PLACEHOLDER_RE.findall(source)

        # Merge: frontmatter order takes priority, body vars fill in anything missed
        all_vars = frontmatter_vars + [v for v in body_vars if v not in frontmatter_vars]

        slug = path.stem  # filename without extension

        return DocumentTemplate(
            name=name,
            slug=slug,
            description=description,
            file_path=path,
            variables=all_vars,
            category=category,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_templates(self) -> list[DocumentTemplate]:
        """Return all loaded templates sorted by category then name."""
        return sorted(self._templates.values(), key=lambda t: (t.category, t.name))

    def get_template(self, slug: str) -> DocumentTemplate | None:
        """Return a template by slug, or None if not found."""
        return self._templates.get(slug)

    def render_template(self, slug: str, variables: dict[str, str]) -> str:
        """Fill in all {{placeholder}} values and return the rendered Typst source.

        Args:
            slug: Template slug (filename without .typ).
            variables: Dict mapping placeholder names to their values.

        Returns:
            Rendered Typst source string ready for compilation.

        Raises:
            KeyError: If the slug is not found.
            ValueError: If required variables are missing.
        """
        template = self._templates.get(slug)
        if template is None:
            available = ", ".join(self._templates.keys()) or "(none)"
            raise KeyError(f"Template '{slug}' not found. Available: {available}")

        source = template.file_path.read_text(encoding="utf-8")

        # Detect missing variables (warn but don't hard-fail — LLM may provide extras)
        missing = [v for v in template.variables if v not in variables]
        if missing:
            log.warning(
                "template_missing_variables",
                slug=slug,
                missing=missing,
            )

        def _replace(match: re.Match[str]) -> str:
            key = match.group(1)
            return variables.get(key, match.group(0))  # keep {{var}} if not provided

        rendered = _PLACEHOLDER_RE.sub(_replace, source)
        return rendered

    def get_template_info(self, slug: str) -> str:
        """Return a human-readable description of a template."""
        template = self._templates.get(slug)
        if template is None:
            return f"Template '{slug}' nicht gefunden."

        lines = [
            f"Template: {template.name} (slug: {template.slug})",
            f"Kategorie: {template.category}",
            f"Beschreibung: {template.description}",
            f"Variablen ({len(template.variables)}): {', '.join(template.variables)}",
            f"Datei: {template.file_path}",
        ]
        return "\n".join(lines)

    def list_as_json(self) -> list[dict[str, Any]]:
        """Return template metadata as a JSON-serialisable list."""
        return [
            {
                "slug": t.slug,
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "variables": t.variables,
            }
            for t in self.list_templates()
        ]
