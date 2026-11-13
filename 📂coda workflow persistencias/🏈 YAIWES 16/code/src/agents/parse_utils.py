"""
Shared JSON parsing utility for all agents.
Handles Claude's tendency to include analysis text before/around JSON.
"""

import json
import re
import logging

logger = logging.getLogger(__name__)


def parse_agent_response(response_text: str) -> dict:
    """
    Parse Claude's response into a structured decision dict.

    Handles multiple formats:
    1. Pure JSON
    2. JSON wrapped in markdown code fences
    3. Free-form text followed by JSON
    4. JSON embedded anywhere in the response

    Returns:
        Parsed dict with keys: reasoning, command, phase_complete, findings, etc.

    Raises:
        json.JSONDecodeError if no valid JSON found
    """
    cleaned = response_text.strip()

    # Strategy 1: Direct JSON parse (ideal case)
    if cleaned.startswith("{"):
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

    # Strategy 2: JSON in markdown code fences
    #   ```json\n{...}\n```  or  ```\n{...}\n```
    fence_match = re.search(
        r"```(?:json)?\s*\n?(\{.*?\})\s*\n?```", cleaned, re.DOTALL
    )
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: Find all complete JSON objects and try the best one
    # Claude often puts analysis text before the JSON
    brace_depth = 0
    json_start = -1
    json_candidates = []

    for i, char in enumerate(cleaned):
        if char == "{":
            if brace_depth == 0:
                json_start = i
            brace_depth += 1
        elif char == "}":
            brace_depth -= 1
            if brace_depth == 0 and json_start != -1:
                json_candidates.append(cleaned[json_start : i + 1])
                json_start = -1

    # Try candidates from last to first (the actual JSON response is usually last)
    for candidate in reversed(json_candidates):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and (
                "command" in parsed or "reasoning" in parsed
            ):
                return parsed
        except json.JSONDecodeError:
            continue

    # Strategy 4: Try to find any JSON-like structure with known keys
    simple_match = re.search(
        r'\{[^{}]*"(?:command|reasoning)"[^{}]*\}', cleaned, re.DOTALL
    )
    if simple_match:
        try:
            return json.loads(simple_match.group(0))
        except json.JSONDecodeError:
            pass

    raise json.JSONDecodeError(
        f"No valid JSON found in response ({len(cleaned)} chars)",
        cleaned[:200],
        0,
    )
