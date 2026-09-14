"""Tests for Phase 0: query preprocessing."""

from mmem.retrieval.query_preprocessor import PreprocessedQuery, preprocess_query


class TestTemporalDetection:
    def test_when_query(self):
        pq = preprocess_query("When did Alice join Acme?")
        assert "temporal" in pq.query_type_hints

    def test_before_query(self):
        pq = preprocess_query("What happened before Alice left?")
        assert "temporal" in pq.query_type_hints

    def test_chinese_temporal(self):
        pq = preprocess_query("Alice 什么时候加入了公司？")
        assert "temporal" in pq.query_type_hints


class TestCausalDetection:
    def test_why_query(self):
        pq = preprocess_query("Why did Alice leave Acme?")
        assert "causal" in pq.query_type_hints

    def test_because_query(self):
        pq = preprocess_query("Alice left because of the reorganisation")
        assert "causal" in pq.query_type_hints

    def test_chinese_causal(self):
        pq = preprocess_query("Alice 为什么离开了？")
        assert "causal" in pq.query_type_hints


class TestMixedQuery:
    def test_temporal_and_causal(self):
        pq = preprocess_query("When and why did Alice leave Acme?")
        assert "temporal" in pq.query_type_hints
        assert "causal" in pq.query_type_hints

    def test_temporal_and_causal_no_general(self):
        pq = preprocess_query("When and why did Alice leave Acme?")
        assert "general" not in pq.query_type_hints


class TestEntityCentric:
    def test_short_query(self):
        pq = preprocess_query("Alice Bob")
        assert "entity_centric" in pq.query_type_hints

    def test_single_word(self):
        pq = preprocess_query("Alice")
        assert "entity_centric" in pq.query_type_hints


class TestGeneralFallback:
    def test_generic_query(self):
        pq = preprocess_query("Tell me everything about the project progress")
        assert "general" in pq.query_type_hints

    def test_no_temporal_no_causal(self):
        pq = preprocess_query("Describe Alice's career at Acme Corp in detail")
        assert "temporal" not in pq.query_type_hints
        assert "causal" not in pq.query_type_hints


class TestQuestionWordStripping:
    def test_strip_what_is(self):
        pq = preprocess_query("What is Alice's role?")
        assert "what is" not in pq.vector_query.lower()
        assert "alice" in pq.vector_query.lower()

    def test_strip_tell_me_about(self):
        pq = preprocess_query("Tell me about Bob's job")
        assert "tell me about" not in pq.vector_query.lower()
        assert "bob" in pq.vector_query.lower()

    def test_strip_trailing_question_mark(self):
        pq = preprocess_query("What is Alice's role?")
        assert not pq.vector_query.endswith("?")

    def test_preserves_original(self):
        pq = preprocess_query("What is Alice's role?")
        assert pq.original == "What is Alice's role?"

    def test_fallback_when_all_stripped(self):
        pq = preprocess_query("What is?")
        assert len(pq.vector_query) > 0
