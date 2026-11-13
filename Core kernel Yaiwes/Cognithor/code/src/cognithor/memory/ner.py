"""Enhanced Named Entity Recognition and Relationship Extraction.

Extends the existing German NER heuristics with:
- Relationship extraction (causal, temporal, hierarchical, contradicts)
- Confidence scoring (user-confirmed vs. LLM-inferred)
- Entity deduplication / alias merging
- Automatic conversation entity extraction for the knowledge graph

Architecture: §8.3 (Knowledge Graph NER)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

# ---------------------------------------------------------------------------
# Relationship Types
# ---------------------------------------------------------------------------


class RelationType(StrEnum):
    """Extended relationship types for the knowledge graph."""

    # Structural
    WORKS_AT = "arbeitet_bei"
    HAS_ROLE = "hat_rolle"
    BELONGS_TO = "gehoert_zu"
    PART_OF = "teil_von"
    OWNS = "besitzt"

    # Hierarchical
    IS_A = "ist_ein"
    PARENT_OF = "uebergeordnet"
    CHILD_OF = "untergeordnet"

    # Causal
    CAUSES = "verursacht"
    CAUSED_BY = "verursacht_durch"
    ENABLES = "ermoeglicht"
    PREVENTS = "verhindert"

    # Temporal
    BEFORE = "vor"
    AFTER = "nach"
    DURING = "waehrend"
    STARTED_AT = "begonnen_am"
    ENDED_AT = "beendet_am"

    # Semantic
    RELATED_TO = "verwandt_mit"
    SIMILAR_TO = "aehnlich_wie"
    CONTRADICTS = "widerspricht"
    SUPPORTS = "unterstuetzt"
    DEPENDS_ON = "abhaengig_von"

    # Social
    KNOWS = "kennt"
    COLLABORATES_WITH = "arbeitet_zusammen_mit"
    MANAGES = "leitet"
    REPORTS_TO = "berichtet_an"


# ---------------------------------------------------------------------------
# Confidence Source
# ---------------------------------------------------------------------------


class ConfidenceSource(StrEnum):
    """How confident we are about an entity or relation."""

    USER_CONFIRMED = "user_confirmed"  # 1.0
    LLM_INFERRED = "llm_inferred"  # 0.7
    HEURISTIC = "heuristic"  # 0.5
    PATTERN_MATCH = "pattern_match"  # 0.6
    IMPORTED = "imported"  # 0.8


CONFIDENCE_SCORES: dict[ConfidenceSource, float] = {
    ConfidenceSource.USER_CONFIRMED: 1.0,
    ConfidenceSource.LLM_INFERRED: 0.7,
    ConfidenceSource.HEURISTIC: 0.5,
    ConfidenceSource.PATTERN_MATCH: 0.6,
    ConfidenceSource.IMPORTED: 0.8,
}


# ---------------------------------------------------------------------------
# Extracted entities and relations
# ---------------------------------------------------------------------------


@dataclass
class ExtractedEntity:
    """An entity extracted from text."""

    name: str
    entity_type: str = "unknown"  # person, organization, location, product, concept
    confidence: float = 0.5
    source: ConfidenceSource = ConfidenceSource.HEURISTIC
    aliases: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedRelation:
    """A relationship extracted between two entities."""

    source_name: str
    relation_type: RelationType
    target_name: str
    confidence: float = 0.5
    source: ConfidenceSource = ConfidenceSource.HEURISTIC
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """Result of entity/relation extraction from text."""

    entities: list[ExtractedEntity] = field(default_factory=list)
    relations: list[ExtractedRelation] = field(default_factory=list)
    text_length: int = 0


# ---------------------------------------------------------------------------
# Patterns for entity type classification
# ---------------------------------------------------------------------------

_PERSON_PATTERNS = re.compile(
    r"\b(Herr|Frau|Dr\.|Prof\.|Hr\.|Fr\.)\s+([A-ZÄÖÜ][a-zäöüß]+)", re.UNICODE
)
_ORG_PATTERNS = re.compile(
    r"\b([A-ZÄÖÜ][a-zäöüß]*(?:\s+[A-ZÄÖÜ][a-zäöüß]*)*)\s+"
    r"(GmbH|AG|SE|e\.V\.|Inc\.|Corp\.|Ltd\.|KG|OHG|UG)\b",
    re.UNICODE,
)
_LOCATION_KEYWORDS = frozenset(
    {
        "Berlin",
        "München",
        "Hamburg",
        "Frankfurt",
        "Köln",
        "Stuttgart",
        "Düsseldorf",
        "Wien",
        "Zürich",
        "Bern",
        "Deutschland",
        "Österreich",
        "Schweiz",
        "Europa",
        "USA",
        "China",
        "Japan",
    }
)
_PRODUCT_INDICATORS = re.compile(
    r"\b(Version|v\d|Release|Update|Plugin|App|Tool|Software|Plattform|System)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Relationship extraction patterns
# ---------------------------------------------------------------------------

_CAUSAL_PATTERNS = [
    (
        re.compile(r"(.+?)\s+(?:verursacht|führt zu|bewirkt)\s+(.+)", re.IGNORECASE),
        RelationType.CAUSES,
    ),
    (re.compile(r"(.+?)\s+(?:verhindert|blockiert)\s+(.+)", re.IGNORECASE), RelationType.PREVENTS),
    (re.compile(r"(.+?)\s+(?:ermöglicht|erlaubt)\s+(.+)", re.IGNORECASE), RelationType.ENABLES),
    (
        re.compile(r"(.+?)\s+(?:widerspricht|widerlegt)\s+(.+)", re.IGNORECASE),
        RelationType.CONTRADICTS,
    ),
    (
        re.compile(r"(.+?)\s+(?:unterstützt|bestätigt|bekräftigt)\s+(.+)", re.IGNORECASE),
        RelationType.SUPPORTS,
    ),
]

_STRUCTURAL_PATTERNS = [
    (
        re.compile(r"(.+?)\s+(?:arbeitet bei|ist bei|arbeitet für)\s+(.+)", re.IGNORECASE),
        RelationType.WORKS_AT,
    ),
    (
        re.compile(r"(.+?)\s+(?:ist|war)\s+(.+?)(?:\s+bei\s+(.+))?$", re.IGNORECASE),
        RelationType.HAS_ROLE,
    ),
    (re.compile(r"(.+?)\s+(?:leitet|führt|managt)\s+(.+)", re.IGNORECASE), RelationType.MANAGES),
    (re.compile(r"(.+?)\s+(?:gehört zu|ist Teil von)\s+(.+)", re.IGNORECASE), RelationType.PART_OF),
    (re.compile(r"(.+?)\s+(?:kennt|traf)\s+(.+)", re.IGNORECASE), RelationType.KNOWS),
    (
        re.compile(r"(.+?)\s+(?:hängt ab von|abhängig von|braucht)\s+(.+)", re.IGNORECASE),
        RelationType.DEPENDS_ON,
    ),
]

# German common nouns to filter (subset — full list in enhanced_retrieval.py)
_COMMON_NOUNS = frozenset(
    {
        "Anfang",
        "Arbeit",
        "Aufgabe",
        "Beispiel",
        "Bericht",
        "Daten",
        "Ende",
        "Ergebnis",
        "Frage",
        "Grund",
        "Information",
        "Jahr",
        "Lösung",
        "Monat",
        "Name",
        "Problem",
        "Projekt",
        "Sache",
        "System",
        "Tag",
        "Teil",
        "Text",
        "Thema",
        "Woche",
        "Zeit",
        "Ziel",
        "Antwort",
        "Bereich",
        "Fall",
        "Form",
        "Gruppe",
        "Hilfe",
        "Idee",
        "Kategorie",
        "Liste",
        "Methode",
        "Nummer",
        "Punkt",
        "Schritt",
        "Seite",
        "Stelle",
        "Typ",
        "Version",
        "Weg",
    }
)

_ENTITY_RE = re.compile(r"\b[A-ZÄÖÜ][a-zäöüß]{2,}\b")
_MULTI_WORD_RE = re.compile(r"\b([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+)\b")


# ---------------------------------------------------------------------------
# Entity Extractor
# ---------------------------------------------------------------------------


class EntityExtractor:
    """Extract entities and relationships from German text."""

    def extract(
        self,
        text: str,
        *,
        source: ConfidenceSource = ConfidenceSource.HEURISTIC,
    ) -> ExtractionResult:
        """Extract entities and relations from text.

        Args:
            text: German text to process.
            source: How confident we are about the extraction.

        Returns:
            ExtractionResult with entities and relations.
        """
        if not text or len(text) < 10:
            return ExtractionResult(text_length=len(text) if text else 0)

        entities = self._extract_entities(text, source)
        relations = self._extract_relations(text, entities, source)

        return ExtractionResult(
            entities=entities,
            relations=relations,
            text_length=len(text),
        )

    def _extract_entities(
        self,
        text: str,
        source: ConfidenceSource,
    ) -> list[ExtractedEntity]:
        """Extract named entities from text."""
        entities: dict[str, ExtractedEntity] = {}
        base_confidence = CONFIDENCE_SCORES.get(source, 0.5)

        # 1. Person names (Herr/Frau + Name)
        for m in _PERSON_PATTERNS.finditer(text):
            name = m.group(2)
            if name not in entities:
                entities[name] = ExtractedEntity(
                    name=name,
                    entity_type="person",
                    confidence=min(base_confidence + 0.2, 1.0),
                    source=source,
                )

        # 2. Organizations (Name + GmbH/AG/...)
        for m in _ORG_PATTERNS.finditer(text):
            full_name = f"{m.group(1)} {m.group(2)}"
            entities[full_name] = ExtractedEntity(
                name=full_name,
                entity_type="organization",
                confidence=min(base_confidence + 0.3, 1.0),
                source=source,
            )

        # 3. Multi-word entities
        for m in _MULTI_WORD_RE.finditer(text):
            name = m.group(1)
            words = name.split()
            if (
                all(w not in _COMMON_NOUNS for w in words)
                and len(words) <= 4
                and name not in entities
            ):
                entities[name] = ExtractedEntity(
                    name=name,
                    entity_type=self._classify_entity(name, text),
                    confidence=base_confidence,
                    source=source,
                )

        # 4. Single-word capitalized entities
        for m in _ENTITY_RE.finditer(text):
            word = m.group(0)
            if word in _COMMON_NOUNS or word in entities:
                continue
            # Skip if it's part of a multi-word entity already captured
            if any(word in e for e in entities if e != word):
                continue
            entities[word] = ExtractedEntity(
                name=word,
                entity_type=self._classify_entity(word, text),
                confidence=max(base_confidence - 0.1, 0.1),
                source=source,
            )

        return list(entities.values())

    def _extract_relations(
        self,
        text: str,
        entities: list[ExtractedEntity],
        source: ConfidenceSource,
    ) -> list[ExtractedRelation]:
        """Extract relationships from text using pattern matching."""
        relations: list[ExtractedRelation] = []
        entity_names = {e.name for e in entities}
        base_confidence = CONFIDENCE_SCORES.get(source, 0.5)

        # Split into sentences
        sentences = re.split(r"[.!?]\s+", text)

        for sentence in sentences:
            # Try causal patterns
            for pattern, rel_type in _CAUSAL_PATTERNS:
                m = pattern.search(sentence)
                if m:
                    src = self._find_entity_in_text(m.group(1), entity_names)
                    tgt = self._find_entity_in_text(m.group(2), entity_names)
                    if src and tgt and src != tgt:
                        relations.append(
                            ExtractedRelation(
                                source_name=src,
                                relation_type=rel_type,
                                target_name=tgt,
                                confidence=base_confidence,
                                source=source,
                            )
                        )

            # Try structural patterns
            for pattern, rel_type in _STRUCTURAL_PATTERNS:
                m = pattern.search(sentence)
                if m:
                    src = self._find_entity_in_text(m.group(1), entity_names)
                    tgt = self._find_entity_in_text(m.group(2), entity_names)
                    if src and tgt and src != tgt:
                        relations.append(
                            ExtractedRelation(
                                source_name=src,
                                relation_type=rel_type,
                                target_name=tgt,
                                confidence=base_confidence,
                                source=source,
                            )
                        )

        return relations

    def _classify_entity(self, name: str, context: str) -> str:
        """Classify entity type based on name and context."""
        if name in _LOCATION_KEYWORDS:
            return "location"
        if _ORG_PATTERNS.search(f"{name} GmbH"):
            return "organization"
        if _PRODUCT_INDICATORS.search(
            context[max(0, context.find(name) - 50) : context.find(name) + 50 + len(name)]
        ):
            return "product"
        return "unknown"

    def _find_entity_in_text(
        self,
        text_fragment: str,
        entity_names: set[str],
    ) -> str | None:
        """Find the best matching entity name in a text fragment."""
        text_fragment = text_fragment.strip()
        # Exact match
        if text_fragment in entity_names:
            return text_fragment
        # Partial match (entity name is contained in fragment)
        for name in entity_names:
            if name in text_fragment:
                return name
        return None


# ---------------------------------------------------------------------------
# Entity Deduplicator
# ---------------------------------------------------------------------------


class EntityDeduplicator:
    """Merge duplicate entities based on name similarity."""

    def __init__(self) -> None:
        self._aliases: dict[str, str] = {}  # alias → canonical name

    def register_alias(self, alias: str, canonical: str) -> None:
        """Register a name as an alias for a canonical entity."""
        self._aliases[alias.lower()] = canonical

    def resolve(self, name: str) -> str:
        """Resolve a name to its canonical form."""
        return self._aliases.get(name.lower(), name)

    def find_duplicates(
        self,
        entities: list[ExtractedEntity],
    ) -> list[tuple[str, str]]:
        """Find potential duplicate entity pairs.

        Uses simple heuristics:
        - Prefix matching (Alex → Alexander)
        - Case-insensitive matching
        - Common abbreviation patterns
        """
        pairs: list[tuple[str, str]] = []
        names = [e.name for e in entities]

        for i, name_a in enumerate(names):
            for name_b in names[i + 1 :]:
                if self._is_potential_duplicate(name_a, name_b):
                    pairs.append((name_a, name_b))

        return pairs

    def merge_entities(
        self,
        entities: list[ExtractedEntity],
    ) -> list[ExtractedEntity]:
        """Merge duplicate entities, keeping the highest-confidence version."""
        canonical: dict[str, ExtractedEntity] = {}

        for entity in entities:
            resolved_name = self.resolve(entity.name)
            if resolved_name in canonical:
                existing = canonical[resolved_name]
                if entity.confidence > existing.confidence:
                    # Keep higher confidence, merge aliases
                    aliases = list(set([*existing.aliases, existing.name, entity.name]))
                    canonical[resolved_name] = ExtractedEntity(
                        name=resolved_name,
                        entity_type=entity.entity_type or existing.entity_type,
                        confidence=entity.confidence,
                        source=entity.source,
                        aliases=[a for a in aliases if a != resolved_name],
                        attributes={**existing.attributes, **entity.attributes},
                    )
                else:
                    existing.aliases = list(set([*existing.aliases, entity.name]))
            else:
                canonical[resolved_name] = entity

        return list(canonical.values())

    def _is_potential_duplicate(self, a: str, b: str) -> bool:
        """Check if two names might refer to the same entity."""
        a_lower = a.lower()
        b_lower = b.lower()

        # Exact (case-insensitive)
        if a_lower == b_lower:
            return True

        # Prefix (one is abbreviation of other)
        if (
            len(a) >= 3
            and len(b) >= 3
            and (a_lower.startswith(b_lower) or b_lower.startswith(a_lower))
        ):
            return True

        return False

    @property
    def alias_count(self) -> int:
        return len(self._aliases)
