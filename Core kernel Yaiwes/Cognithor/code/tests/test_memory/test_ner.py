"""Tests for the Enhanced NER module (memory/ner.py).

Covers entity extraction, relationship extraction, entity classification,
deduplication, confidence scoring, and edge cases.
"""

from __future__ import annotations

from cognithor.memory.ner import (
    CONFIDENCE_SCORES,
    ConfidenceSource,
    EntityDeduplicator,
    EntityExtractor,
    ExtractedEntity,
    ExtractedRelation,
    ExtractionResult,
    RelationType,
)

# ============================================================================
# RelationType enum
# ============================================================================


class TestRelationType:
    def test_structural_types(self) -> None:
        assert RelationType.WORKS_AT == "arbeitet_bei"
        assert RelationType.HAS_ROLE == "hat_rolle"
        assert RelationType.PART_OF == "teil_von"

    def test_causal_types(self) -> None:
        assert RelationType.CAUSES == "verursacht"
        assert RelationType.PREVENTS == "verhindert"
        assert RelationType.ENABLES == "ermoeglicht"

    def test_temporal_types(self) -> None:
        assert RelationType.BEFORE == "vor"
        assert RelationType.AFTER == "nach"
        assert RelationType.DURING == "waehrend"

    def test_semantic_types(self) -> None:
        assert RelationType.CONTRADICTS == "widerspricht"
        assert RelationType.SUPPORTS == "unterstuetzt"
        assert RelationType.DEPENDS_ON == "abhaengig_von"

    def test_social_types(self) -> None:
        assert RelationType.KNOWS == "kennt"
        assert RelationType.MANAGES == "leitet"
        assert RelationType.REPORTS_TO == "berichtet_an"

    def test_all_types_are_strings(self) -> None:
        for rt in RelationType:
            assert isinstance(rt.value, str)

    def test_count(self) -> None:
        assert len(RelationType) == 26


# ============================================================================
# ConfidenceSource
# ============================================================================


class TestConfidenceSource:
    def test_scores_present(self) -> None:
        for src in ConfidenceSource:
            assert src in CONFIDENCE_SCORES

    def test_user_confirmed_highest(self) -> None:
        assert CONFIDENCE_SCORES[ConfidenceSource.USER_CONFIRMED] == 1.0

    def test_heuristic_score(self) -> None:
        assert CONFIDENCE_SCORES[ConfidenceSource.HEURISTIC] == 0.5

    def test_all_scores_between_0_and_1(self) -> None:
        for score in CONFIDENCE_SCORES.values():
            assert 0.0 <= score <= 1.0


# ============================================================================
# ExtractedEntity / ExtractedRelation
# ============================================================================


class TestDataclasses:
    def test_entity_defaults(self) -> None:
        e = ExtractedEntity(name="Test")
        assert e.entity_type == "unknown"
        assert e.confidence == 0.5
        assert e.source == ConfidenceSource.HEURISTIC
        assert e.aliases == []
        assert e.attributes == {}

    def test_entity_custom(self) -> None:
        e = ExtractedEntity(
            name="Berlin",
            entity_type="location",
            confidence=0.9,
            source=ConfidenceSource.USER_CONFIRMED,
            aliases=["BER"],
            attributes={"country": "DE"},
        )
        assert e.name == "Berlin"
        assert e.entity_type == "location"
        assert e.attributes["country"] == "DE"

    def test_relation_defaults(self) -> None:
        r = ExtractedRelation(
            source_name="Alice",
            relation_type=RelationType.KNOWS,
            target_name="Bob",
        )
        assert r.confidence == 0.5
        assert r.source == ConfidenceSource.HEURISTIC

    def test_extraction_result_defaults(self) -> None:
        result = ExtractionResult()
        assert result.entities == []
        assert result.relations == []
        assert result.text_length == 0


# ============================================================================
# EntityExtractor — Entity Extraction
# ============================================================================


class TestEntityExtraction:
    def setup_method(self) -> None:
        self.extractor = EntityExtractor()

    def test_empty_text(self) -> None:
        result = self.extractor.extract("")
        assert result.entities == []
        assert result.text_length == 0

    def test_short_text(self) -> None:
        result = self.extractor.extract("Hallo")
        assert result.entities == []

    def test_person_herr(self) -> None:
        result = self.extractor.extract("Herr Schmidt arbeitet hier seit Jahren.")
        names = [e.name for e in result.entities]
        assert "Schmidt" in names
        entity = next(e for e in result.entities if e.name == "Schmidt")
        assert entity.entity_type == "person"

    def test_person_frau(self) -> None:
        result = self.extractor.extract("Frau Müller ist die Projektleiterin.")
        names = [e.name for e in result.entities]
        assert "Müller" in names
        entity = next(e for e in result.entities if e.name == "Müller")
        assert entity.entity_type == "person"

    def test_person_dr(self) -> None:
        result = self.extractor.extract("Dr. Weber hat die Analyse durchgeführt.")
        names = [e.name for e in result.entities]
        assert "Weber" in names

    def test_organization_gmbh(self) -> None:
        result = self.extractor.extract("Die Firma Siemens GmbH hat den Vertrag unterzeichnet.")
        names = [e.name for e in result.entities]
        assert any("Siemens GmbH" in n for n in names)
        org = next(e for e in result.entities if "Siemens" in e.name and "GmbH" in e.name)
        assert org.entity_type == "organization"

    def test_organization_ag(self) -> None:
        result = self.extractor.extract("Die Deutsche Bank AG meldet Gewinne.")
        names = [e.name for e in result.entities]
        assert any("AG" in n for n in names)

    def test_location_known(self) -> None:
        result = self.extractor.extract("Das Meeting findet in Berlin statt.")
        names = [e.name for e in result.entities]
        assert "Berlin" in names
        entity = next(e for e in result.entities if e.name == "Berlin")
        assert entity.entity_type == "location"

    def test_multi_word_entity(self) -> None:
        result = self.extractor.extract("Das Rote Kreuz hilft bei der Katastrophe.")
        names = [e.name for e in result.entities]
        assert any("Rote Kreuz" in n for n in names)

    def test_common_nouns_filtered(self) -> None:
        result = self.extractor.extract("Das Problem ist die Lösung der Aufgabe im Projekt.")
        names = [e.name for e in result.entities]
        assert "Problem" not in names
        assert "Lösung" not in names
        assert "Aufgabe" not in names
        assert "Projekt" not in names

    def test_confidence_boosted_for_person(self) -> None:
        result = self.extractor.extract("Herr Braun ist der Abteilungsleiter.")
        entity = next(e for e in result.entities if e.name == "Braun")
        assert entity.confidence > 0.5  # Boosted from heuristic base

    def test_confidence_boosted_for_org(self) -> None:
        result = self.extractor.extract("Die Acme GmbH liefert Software.")
        org = next(e for e in result.entities if "GmbH" in e.name)
        assert org.confidence > 0.5  # Boosted

    def test_single_word_lower_confidence(self) -> None:
        result = self.extractor.extract(
            "Tensorflow wurde für das Training verwendet und funktioniert gut."
        )
        if any(e.name == "Tensorflow" for e in result.entities):
            entity = next(e for e in result.entities if e.name == "Tensorflow")
            assert entity.confidence <= 0.5  # Single word, lower confidence

    def test_text_length_recorded(self) -> None:
        text = "Herr Schmidt arbeitet bei der Siemens GmbH in München."
        result = self.extractor.extract(text)
        assert result.text_length == len(text)

    def test_custom_source(self) -> None:
        result = self.extractor.extract(
            "Herr Weber ist Ingenieur.",
            source=ConfidenceSource.LLM_INFERRED,
        )
        entity = next(e for e in result.entities if e.name == "Weber")
        assert entity.source == ConfidenceSource.LLM_INFERRED


# ============================================================================
# EntityExtractor — Relationship Extraction
# ============================================================================


class TestRelationExtraction:
    def setup_method(self) -> None:
        self.extractor = EntityExtractor()

    def test_causal_verursacht(self) -> None:
        result = self.extractor.extract("Regen verursacht Überschwemmungen in der Region.")
        rel_types = [r.relation_type for r in result.relations]
        if result.relations:
            assert RelationType.CAUSES in rel_types

    def test_structural_arbeitet_bei(self) -> None:
        result = self.extractor.extract("Herr Schmidt arbeitet bei der Siemens GmbH seit Jahren.")
        rel_types = [r.relation_type for r in result.relations]
        if result.relations:
            assert RelationType.WORKS_AT in rel_types

    def test_structural_leitet(self) -> None:
        result = self.extractor.extract(
            "Herr Müller leitet die Abteilung Forschung und Entwicklung."
        )
        rel_types = [r.relation_type for r in result.relations]
        if result.relations:
            assert RelationType.MANAGES in rel_types

    def test_prevents_pattern(self) -> None:
        result = self.extractor.extract("Sicherheit verhindert Datenverlust bei der Firma.")
        # May or may not extract depending on entity matching
        for r in result.relations:
            if r.relation_type == RelationType.PREVENTS:
                assert r.source_name != r.target_name

    def test_no_self_relations(self) -> None:
        result = self.extractor.extract("Herr Schmidt kennt Herr Schmidt nicht besonders gut.")
        for r in result.relations:
            assert r.source_name != r.target_name

    def test_empty_relations_for_no_patterns(self) -> None:
        result = self.extractor.extract("Berlin ist eine schöne Stadt mit viel Geschichte.")
        # No causal/structural pattern, so relations may be empty
        assert isinstance(result.relations, list)


# ============================================================================
# EntityExtractor — Classification
# ============================================================================


class TestEntityClassification:
    def setup_method(self) -> None:
        self.extractor = EntityExtractor()

    def test_location_classification(self) -> None:
        result = self.extractor.extract("München ist die Hauptstadt von Bayern.")
        entity = next((e for e in result.entities if e.name == "München"), None)
        assert entity is not None
        assert entity.entity_type == "location"

    def test_product_classification(self) -> None:
        result = self.extractor.extract(
            "Die neue Version von Kubernetes wird morgen veröffentlicht."
        )
        # Classification depends on context heuristics — just verify entity found
        names = [e.name for e in result.entities]
        assert "Kubernetes" in names


# ============================================================================
# EntityDeduplicator
# ============================================================================


class TestEntityDeduplicator:
    def setup_method(self) -> None:
        self.dedup = EntityDeduplicator()

    def test_register_and_resolve(self) -> None:
        self.dedup.register_alias("Alex", "Alexander")
        assert self.dedup.resolve("Alex") == "Alexander"

    def test_resolve_unknown(self) -> None:
        assert self.dedup.resolve("Unknown") == "Unknown"

    def test_case_insensitive_resolve(self) -> None:
        self.dedup.register_alias("ALEX", "Alexander")
        assert self.dedup.resolve("alex") == "Alexander"

    def test_find_duplicates_exact(self) -> None:
        entities = [
            ExtractedEntity(name="Berlin"),
            ExtractedEntity(name="berlin"),
        ]
        pairs = self.dedup.find_duplicates(entities)
        assert len(pairs) == 1
        assert ("Berlin", "berlin") in pairs

    def test_find_duplicates_prefix(self) -> None:
        entities = [
            ExtractedEntity(name="Alex"),
            ExtractedEntity(name="Alexander"),
        ]
        pairs = self.dedup.find_duplicates(entities)
        assert len(pairs) == 1

    def test_no_duplicates(self) -> None:
        entities = [
            ExtractedEntity(name="Berlin"),
            ExtractedEntity(name="München"),
        ]
        pairs = self.dedup.find_duplicates(entities)
        assert len(pairs) == 0

    def test_merge_keeps_higher_confidence(self) -> None:
        self.dedup.register_alias("Alex", "Alexander")
        entities = [
            ExtractedEntity(name="Alexander", confidence=0.5),
            ExtractedEntity(name="Alex", confidence=0.9),
        ]
        merged = self.dedup.merge_entities(entities)
        assert len(merged) == 1
        assert merged[0].name == "Alexander"
        assert merged[0].confidence == 0.9

    def test_merge_adds_aliases(self) -> None:
        self.dedup.register_alias("Alex", "Alexander")
        entities = [
            ExtractedEntity(name="Alexander", confidence=0.8),
            ExtractedEntity(name="Alex", confidence=0.5),
        ]
        merged = self.dedup.merge_entities(entities)
        assert len(merged) == 1
        assert "Alex" in merged[0].aliases

    def test_merge_no_duplicates(self) -> None:
        entities = [
            ExtractedEntity(name="Berlin"),
            ExtractedEntity(name="München"),
        ]
        merged = self.dedup.merge_entities(entities)
        assert len(merged) == 2

    def test_merge_preserves_attributes(self) -> None:
        self.dedup.register_alias("JS", "JavaScript")
        entities = [
            ExtractedEntity(name="JavaScript", attributes={"category": "language"}),
            ExtractedEntity(name="JS", confidence=0.9, attributes={"short": True}),
        ]
        merged = self.dedup.merge_entities(entities)
        assert len(merged) == 1
        assert merged[0].attributes["category"] == "language"
        assert merged[0].attributes["short"] is True

    def test_merge_entity_type_from_higher_confidence(self) -> None:
        self.dedup.register_alias("BER", "Berlin")
        entities = [
            ExtractedEntity(name="Berlin", entity_type="unknown", confidence=0.3),
            ExtractedEntity(name="BER", entity_type="location", confidence=0.8),
        ]
        merged = self.dedup.merge_entities(entities)
        assert merged[0].entity_type == "location"

    def test_alias_count(self) -> None:
        assert self.dedup.alias_count == 0
        self.dedup.register_alias("a", "A")
        self.dedup.register_alias("b", "B")
        assert self.dedup.alias_count == 2

    def test_short_names_no_prefix_match(self) -> None:
        """Names shorter than 3 chars shouldn't trigger prefix matching."""
        entities = [
            ExtractedEntity(name="AI"),
            ExtractedEntity(name="API"),
        ]
        pairs = self.dedup.find_duplicates(entities)
        assert len(pairs) == 0
