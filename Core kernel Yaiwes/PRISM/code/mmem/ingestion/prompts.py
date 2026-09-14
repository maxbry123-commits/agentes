"""
Prompt templates for ingestion-time information extraction.

This module intentionally contains only string templates and no business logic.
"""

EXTRACTION_PROMPT = """You are an information extraction engine.

Task:
Extract structured memory data from the text chunk below.

Text chunk:
{chunk}

Return a single JSON object with exactly these top-level keys:
- episode_summary: string
- entities: array of objects
- facet_points: array of objects
- facets: array of objects
- temporal_info: array of objects

Schema details:
1) episode_summary
- A concise but comprehensive summary of ALL events and facts mentioned in the chunk. Include specific details like names, dates, places, objects, and quantities.

2) entities
- Each item must be:
  {{
    "name": string,
    "entity_type": string
  }}
- entity_type should be one of: "person", "organization", "place", "concept", "event", "other".
- Keep names as they appear in the text whenever possible.
- Include specific items mentioned (books, foods, activities, pets, places visited, etc.) as entities with type "concept" or "other".

3) facet_points
- Each item must be:
  {{
    "content": string,
    "related_entity_name": string or null,
    "timestamp_text": string or null
  }}
- content should be atomic and factual.
- IMPORTANT: Be specific. Include concrete details like exact names, quantities, colors, and descriptions.
  Good: "Melanie made a cup in her pottery class"
  Bad: "Melanie does pottery"
  Good: "Caroline recommended the book Becoming Nicole to Melanie"
  Bad: "Caroline recommended a book"
  Good: "Melanie and her family saw the Perseid meteor shower during their camping trip"
  Bad: "Melanie went camping"
- Extract every distinct fact as a separate facet_point. Do not merge multiple facts into one.

4) facets
- Each item must be:
  {{
    "theme": string,
    "facet_point_indices": array of integers
  }}
- facet_point_indices refers to zero-based indices in the facet_points array.

5) temporal_info
- Each item must be:
  {{
    "subject": string,
    "time_expression": string,
    "normalized_time": string or null,
    "relation": string
  }}
- relation examples: "before", "after", "during", "at".
- normalized_time should use ISO-8601 when explicit enough, otherwise null.
- For relative time references (e.g., "yesterday", "last week"), use the conversation timestamp shown in the chunk header to compute an absolute date for normalized_time.

Rules:
- Output valid JSON only. No markdown fences, no explanation text.
- If information is missing, use empty arrays or null values as appropriate.
- Do not invent unsupported facts.
- Prefer extracting MORE facet_points with specific details over fewer generic ones.
"""


CAUSAL_PROMPT = """You are a causal reasoning engine.

Task:
Given a list of episode summaries, identify likely causal relations.

Events:
{events}

Return a single JSON object with exactly one top-level key:
- causal_pairs: array of objects

Each causal_pairs item must be:
{{
  "cause_id": string,
  "effect_id": string,
  "description": string,
  "confidence": number
}}

Rules:
- cause_id and effect_id must refer to event IDs provided in the input.
- confidence must be between 0.0 and 1.0.
- Keep descriptions concise and evidence-aware.
- Only include relations with meaningful support from the provided events.
- Output valid JSON only. No markdown fences, no explanation text.
- If no reliable causal relation exists, return: {{"causal_pairs": []}}.
"""


FALLBACK_EXTRACTION_PROMPT = """You are a lightweight information extraction engine.

Task:
Extract only a concise episode summary and entity list from the text chunk.

Text chunk:
{chunk}

Return a single JSON object with exactly these keys:
- episode_summary: string
- entities: array of objects

Each entities item must be:
{{
  "name": string,
  "entity_type": string
}}

Rules:
- entity_type should be one of: "person", "organization", "place", "concept", "event", "other".
- Output valid JSON only. No markdown fences, no explanation text.
- If no entities are present, return an empty array.
"""


KEY_SENTENCES_PROMPT = """From the following text chunk, extract the 2-3 sentences that contain the most specific factual information (names, dates, places, objects, quantities, activities).

Do NOT paraphrase. Copy each sentence verbatim from the text.

Text chunk:
{chunk}

Return a JSON array of strings, each being one key sentence.
Example: ["Caroline went to a LGBTQ support group yesterday.", "Melanie ran a charity race for mental health last Saturday."]

Return ONLY the JSON array, no other text."""


__all__ = [
    "EXTRACTION_PROMPT",
    "CAUSAL_PROMPT",
    "FALLBACK_EXTRACTION_PROMPT",
    "KEY_SENTENCES_PROMPT",
]

