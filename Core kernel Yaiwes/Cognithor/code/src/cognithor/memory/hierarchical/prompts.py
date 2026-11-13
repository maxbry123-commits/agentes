"""Prompt templates for LLM-driven node selection."""

from __future__ import annotations

PROMPT_DE = """\
Du bist ein Dokumenten-Navigator. Der Benutzer sucht nach Informationen zu:

**Frage:** {query}

Hier sind die verfuegbaren Abschnitte:

{children_block}

Waehle die relevantesten Abschnitte aus (max. 5). Antworte NUR mit JSON:
{{"selected_node_ids": ["id1", "id2"], "reasoning": "Kurze Begruendung"}}
"""

PROMPT_EN = """\
You are a document navigator. The user is looking for information about:

**Query:** {query}

Here are the available sections:

{children_block}

Select the most relevant sections (max. 5). Reply ONLY with JSON:
{{"selected_node_ids": ["id1", "id2"], "reasoning": "Brief reasoning"}}
"""


def format_selection_prompt(
    query: str,
    children: list[tuple[str, str, str]],
    language: str = "de",
) -> str:
    """Format a node-selection prompt.

    Parameters
    ----------
    query:
        The user's search query.
    children:
        List of ``(node_id, title, summary)`` tuples.
    language:
        ``"de"`` for German, anything else for English.
    """
    lines: list[str] = []
    for node_id, title, summary in children:
        lines.append(f"- **{node_id}**: {title} -- {summary}")

    children_block = "\n".join(lines)
    template = PROMPT_DE if language == "de" else PROMPT_EN
    return template.format(query=query, children_block=children_block)
