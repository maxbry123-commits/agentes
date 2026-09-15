from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from agents.literature_memory_agent import LiteratureMemoryPersistenceAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from memory.literature_memory import LiteratureMemoryStore
from schemas.topic_pack import TopicPack


def _make_topic(name: str = "test_topic") -> TopicPack:
    return TopicPack(
        topic_name=name,
        codebase={"repo_path": "/fake"},
    )


def _make_context(tmp_path: str) -> AgentContext:
    return AgentContext(
        artifact_store=ArtifactStore(Path(tmp_path)),
        memory_store=None,  # type: ignore
        tool_registry=None,  # type: ignore
        settings={},
    )


class LiteratureMemoryStoreTest(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test_lit.db"
        self.store = LiteratureMemoryStore(self.db_path)
        self.scope = "test_topic"

    def tearDown(self):
        self.tmp.cleanup()

    def test_write_and_retrieve_paper(self):
        paper = {
            "paper_id": "paper_001",
            "title": "Diffusion Models for Trajectory Prediction",
            "abstract": "We propose a novel diffusion-based method for pedestrian trajectory prediction.",
            "authors": ["Alice", "Bob"],
            "year": 2024,
            "keywords": ["diffusion", "trajectory", "pedestrian"],
        }
        self.store.write_paper(paper, self.scope)
        results = self.store.retrieve_papers(self.scope, "diffusion", limit=5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["paper_id"], "paper_001")
        self.assertEqual(results[0]["title"], paper["title"])

    def test_write_and_retrieve_method_card_by_task(self):
        card = {
            "method_card_id": "method_001",
            "paper_id": "paper_001",
            "task": "pedestrian trajectory prediction",
            "problem_setting": "multimodal forecasting",
            "input_modalities": ["trajectory", "intention"],
            "model_architecture": {"type": "diffusion"},
            "fusion_strategy": {"type": "cross-attention"},
            "training_objective": "minADE",
            "datasets": ["VIRAT", "ETH/UCY"],
            "metrics": ["ADE", "FDE"],
            "main_results": "ADE=0.23 on VIRAT",
            "limitations": ["slow inference"],
            "reusable_ideas": ["intention conditioning improves accuracy"],
            "implementation_difficulty": "medium",
            "risk": ["data dependency"],
            "evidence_ids": ["ev_1"],
        }
        self.store.write_method_card(card, self.scope)

        results = self.store.retrieve_method_cards(
            self.scope, task="trajectory prediction", limit=5
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["task"], card["task"])

    def test_retrieve_method_card_by_dataset(self):
        card = {
            "method_card_id": "method_002",
            "paper_id": "paper_002",
            "task": "forecasting",
            "datasets": ["VIRAT"],
            "metrics": ["ADE"],
        }
        self.store.write_method_card(card, self.scope)
        results = self.store.retrieve_method_cards(self.scope, dataset="VIRAT", limit=5)
        self.assertEqual(len(results), 1)

    def test_retrieve_method_card_by_metric(self):
        card = {
            "method_card_id": "method_003",
            "paper_id": "paper_003",
            "task": "prediction",
            "datasets": ["ETH"],
            "metrics": ["FDE", "miss_rate"],
        }
        self.store.write_method_card(card, self.scope)
        results = self.store.retrieve_method_cards(self.scope, metric="FDE", limit=5)
        self.assertEqual(len(results), 1)

    def test_retrieve_method_card_by_fusion_strategy(self):
        card = {
            "method_card_id": "method_004",
            "paper_id": "paper_004",
            "task": "prediction",
            "datasets": [],
            "metrics": [],
            "fusion_strategy": {"type": "cross-attention"},
        }
        self.store.write_method_card(card, self.scope)
        results = self.store.retrieve_method_cards(
            self.scope, fusion_strategy="cross-attention", limit=5
        )
        self.assertEqual(len(results), 1)

    def test_retrieve_by_topic_keywords(self):
        card = {
            "method_card_id": "method_005",
            "paper_id": "paper_005",
            "task": "language-conditioned pedestrian trajectory prediction",
            "datasets": [],
            "metrics": [],
        }
        self.store.write_method_card(card, self.scope)
        results = self.store.retrieve_method_cards(
            self.scope, topic_keywords=["language", "trajectory"], limit=5
        )
        self.assertEqual(len(results), 1)

    def test_scope_isolation(self):
        card_a = {
            "method_card_id": "method_a",
            "paper_id": "paper_a",
            "task": "topic A task",
            "datasets": [],
            "metrics": [],
        }
        card_b = {
            "method_card_id": "method_b",
            "paper_id": "paper_b",
            "task": "topic B task",
            "datasets": [],
            "metrics": [],
        }
        self.store.write_method_card(card_a, "scope_A")
        self.store.write_method_card(card_b, "scope_B")

        results_a = self.store.retrieve_method_cards("scope_A", limit=10)
        self.assertEqual(len(results_a), 1)
        self.assertEqual(results_a[0]["task"], "topic A task")

        results_b = self.store.retrieve_method_cards("scope_B", limit=10)
        self.assertEqual(len(results_b), 1)
        self.assertEqual(results_b[0]["task"], "topic B task")

    def test_upsert_dedup(self):
        paper = {
            "paper_id": "paper_dup",
            "title": "Original Title",
            "abstract": "abstract",
            "authors": [],
            "year": 2024,
            "keywords": [],
        }
        self.store.write_paper(paper, self.scope)

        paper["title"] = "Updated Title"
        self.store.write_paper(paper, self.scope)

        results = self.store.retrieve_papers(self.scope, limit=10)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Updated Title")

    def test_get_paper_ids_by_scope(self):
        self.store.write_paper(
            {"paper_id": "p1", "title": "T1", "abstract": "", "authors": [], "year": 0, "keywords": []},
            self.scope,
        )
        self.store.write_paper(
            {"paper_id": "p2", "title": "T2", "abstract": "", "authors": [], "year": 0, "keywords": []},
            self.scope,
        )
        self.store.write_paper(
            {"paper_id": "p3", "title": "T3", "abstract": "", "authors": [], "year": 0, "keywords": []},
            "other_scope",
        )
        ids = self.store.get_paper_ids_by_scope(self.scope)
        self.assertEqual(ids, {"p1", "p2"})

    def test_write_run_artifacts(self):
        state_values = {
            "selected_papers": [
                {
                    "paper_id": "paper_run",
                    "title": "Run Paper",
                    "abstract": "test abstract",
                    "authors": ["Author"],
                    "year": 2024,
                    "keywords": ["test"],
                },
            ],
            "method_cards": [
                {
                    "method_card_id": "method_run",
                    "paper_id": "paper_run",
                    "task": "test task",
                    "datasets": ["DS1"],
                    "metrics": ["M1"],
                },
            ],
            "checked_evidence": [
                {
                    "evidence_id": "ev_run",
                    "paper_id": "paper_run",
                    "claim_supported": "claim",
                    "quote": "text",
                    "section": "Method",
                    "support_level": "strong",
                },
            ],
            "parsed_papers": {},
        }
        count = self.store.write_run_artifacts(state_values, self.scope)
        self.assertGreaterEqual(count, 3)

        papers = self.store.retrieve_papers(self.scope, limit=10)
        self.assertEqual(len(papers), 1)

        cards = self.store.retrieve_method_cards(self.scope, limit=10)
        self.assertEqual(len(cards), 1)

        evidence = self.store.retrieve_evidence(self.scope, ["paper_run"], limit=10)
        self.assertEqual(len(evidence), 1)

    def test_retrieve_returns_reusable_ideas_for_current_topic_key(self):
        card = {
            "method_card_id": "method_rkey",
            "paper_id": "paper_rkey",
            "task": "test task",
            "datasets": [],
            "metrics": [],
            "reusable_ideas_for_current_topic": ["idea 1", "idea 2"],
        }
        self.store.write_method_card(card, self.scope)
        results = self.store.retrieve_method_cards(self.scope, task="test task", limit=5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["reusable_ideas_for_current_topic"], ["idea 1", "idea 2"])

    def test_task_normalization_matches_underscore_vs_space(self):
        card = {
            "method_card_id": "method_norm",
            "paper_id": "paper_norm",
            "task": "pedestrian trajectory prediction",
            "datasets": [],
            "metrics": [],
        }
        self.store.write_method_card(card, self.scope)
        # Search with underscore form — should match space form
        results = self.store.retrieve_method_cards(
            self.scope, task="pedestrian_trajectory_prediction", limit=5
        )
        self.assertEqual(len(results), 1)

    def test_retrieval_falls_back_to_keyword_only(self):
        card = {
            "method_card_id": "method_fb",
            "paper_id": "paper_fb",
            "task": "pedestrian trajectory prediction",
            "problem_setting": "multimodal forecasting",
            "datasets": [],
            "metrics": [],
        }
        self.store.write_method_card(card, self.scope)
        # Strict filters that won't match the card
        results = self.store.retrieve_method_cards(
            self.scope,
            task="nonexistent_task_xyz",
            dataset="NonexistentDS",
            topic_keywords=["trajectory", "prediction"],
            limit=5,
        )
        # Should fall back to keyword-only and find the card
        self.assertEqual(len(results), 1)

    def test_write_falls_back_to_reusable_ideas_field(self):
        card = {
            "method_card_id": "method_fb2",
            "paper_id": "paper_fb2",
            "task": "test",
            "datasets": [],
            "metrics": [],
            "reusable_ideas": ["fallback idea"],
        }
        self.store.write_method_card(card, self.scope)
        results = self.store.retrieve_method_cards(self.scope, task="test", limit=5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["reusable_ideas_for_current_topic"], ["fallback idea"])

    # -- P9a: experiment tree persistence -----------------------------------

    def test_write_and_load_branch(self):
        branch = {
            "branch_id": "branch_test_1",
            "root_id": "root_1",
            "status": "active",
            "max_depth": 2,
            "max_active_nodes": 3,
            "nodes": [
                {
                    "node_id": "root_1",
                    "experiment_id": "exp1",
                    "parent_id": "",
                    "hypothesis": "Root hypothesis",
                    "patch_scope": "models/*",
                    "result": {"ade": 0.3},
                    "decision": {"action": "continue"},
                    "children_ids": ["child_1", "child_2"],
                    "status": "active",
                    "depth": 0,
                },
                {
                    "node_id": "child_1",
                    "experiment_id": "exp2",
                    "parent_id": "root_1",
                    "hypothesis": "Child hypothesis",
                    "patch_scope": "data/*",
                    "result": {},
                    "decision": {},
                    "children_ids": [],
                    "status": "pending",
                    "depth": 1,
                },
            ],
        }
        self.store.write_branch(branch, self.scope)
        loaded = self.store.load_branch(self.scope)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["branch_id"], "branch_test_1")
        self.assertEqual(loaded["root_id"], "root_1")
        self.assertEqual(len(loaded["nodes"]), 2)

        root = [n for n in loaded["nodes"] if n["depth"] == 0][0]
        self.assertEqual(root["hypothesis"], "Root hypothesis")
        self.assertEqual(root["result"], {"ade": 0.3})
        self.assertEqual(root["children_ids"], ["child_1", "child_2"])

        child = [n for n in loaded["nodes"] if n["depth"] == 1][0]
        self.assertEqual(child["status"], "pending")

    def test_update_node_result(self):
        branch = {
            "branch_id": "branch_update",
            "root_id": "node_up_1",
            "nodes": [
                {
                    "node_id": "node_up_1",
                    "experiment_id": "exp_up",
                    "parent_id": "",
                    "hypothesis": "H",
                    "patch_scope": "",
                    "result": {},
                    "decision": {},
                    "children_ids": [],
                    "status": "pending",
                    "depth": 0,
                },
            ],
        }
        self.store.write_branch(branch, self.scope)
        self.store.update_node("node_up_1", result={"ade": 0.15}, status="promoted")
        loaded = self.store.load_branch(self.scope)
        node = loaded["nodes"][0]
        self.assertEqual(node["result"], {"ade": 0.15})
        self.assertEqual(node["status"], "promoted")

    def test_update_node_decision_only(self):
        branch = {
            "branch_id": "branch_dec",
            "root_id": "node_dec_1",
            "nodes": [
                {
                    "node_id": "node_dec_1",
                    "experiment_id": "exp_dec",
                    "parent_id": "",
                    "hypothesis": "H",
                    "patch_scope": "",
                    "result": {},
                    "decision": {},
                    "children_ids": [],
                    "status": "pending",
                    "depth": 0,
                },
            ],
        }
        self.store.write_branch(branch, self.scope)
        self.store.update_node("node_dec_1", decision={"action": "rollback"})
        loaded = self.store.load_branch(self.scope)
        self.assertEqual(loaded["nodes"][0]["decision"], {"action": "rollback"})
        # Result and status unchanged
        self.assertEqual(loaded["nodes"][0]["result"], {})
        self.assertEqual(loaded["nodes"][0]["status"], "pending")

    def test_load_returns_none_for_empty_scope(self):
        loaded = self.store.load_branch("nonexistent_scope")
        self.assertIsNone(loaded)

    def test_write_run_artifacts_persists_tree(self):
        state_values = {
            "experiment_tree": {
                "branch_id": "branch_from_run",
                "root_id": "root_run",
                "status": "active",
                "max_depth": 2,
                "max_active_nodes": 3,
                "nodes": [
                    {
                        "node_id": "root_run",
                        "experiment_id": "exp_run",
                        "parent_id": "",
                        "hypothesis": "Run hypothesis",
                        "patch_scope": "trainer/*",
                        "result": {},
                        "decision": {},
                        "children_ids": [],
                        "status": "active",
                        "depth": 0,
                    },
                ],
            },
        }
        count = self.store.write_run_artifacts(state_values, self.scope)
        self.assertGreaterEqual(count, 1)
        loaded = self.store.load_branch(self.scope)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["branch_id"], "branch_from_run")


class LiteratureMemoryPersistenceAgentTest(TestCase):
    def test_persists_run_artifacts(self):
        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            lit_store = LiteratureMemoryStore(db_path)
            agent = LiteratureMemoryPersistenceAgent(lit_memory_store=lit_store)

            topic = _make_topic("test_topic")
            state = ResearchState(topic=topic)
            state.values["selected_papers"] = [
                {
                    "paper_id": "p1",
                    "title": "Test Paper",
                    "abstract": "Test",
                    "authors": [],
                    "year": 2024,
                    "keywords": [],
                },
            ]
            state.values["method_cards"] = [
                {
                    "method_card_id": "mc1",
                    "paper_id": "p1",
                    "task": "test",
                    "datasets": [],
                    "metrics": [],
                },
            ]
            context = _make_context(tmp)
            result = agent.run(state, context)
            self.assertIn("persisted", result.notes[0])

            papers = lit_store.retrieve_papers("test_topic", limit=5)
            self.assertEqual(len(papers), 1)

    def test_noop_when_no_store(self):
        with TemporaryDirectory() as tmp:
            topic = _make_topic()
            state = ResearchState(topic=topic)
            agent = LiteratureMemoryPersistenceAgent(lit_memory_store=None)
            context = _make_context(tmp)
            result = agent.run(state, context)
            self.assertIn("skipped", result.notes[0])

    def test_filter_excludes_unselected_papers_from_memory(self):
        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            lit_store = LiteratureMemoryStore(db_path)
            agent = LiteratureMemoryPersistenceAgent(lit_memory_store=lit_store)

            topic = _make_topic("test_filter")
            state = ResearchState(topic=topic)
            state.values["selected_papers"] = [
                {
                    "paper_id": "keep_me",
                    "title": "Keep This Paper",
                    "abstract": "good",
                    "authors": [],
                    "year": 2024,
                    "keywords": [],
                },
            ]
            state.values["parsed_papers"] = {
                "keep_me": {"paper_id": "keep_me", "sections": []},
                "discard_me": {"paper_id": "discard_me", "sections": []},
            }
            state.values["checked_evidence"] = [
                {"evidence_id": "ev1", "paper_id": "keep_me", "claim_supported": "yes", "quote": "text", "section": "Method", "support_level": "strong"},
                {"evidence_id": "ev2", "paper_id": "discard_me", "claim_supported": "yes", "quote": "text", "section": "Method", "support_level": "strong"},
            ]
            state.values["method_cards"] = [
                {"method_card_id": "mc1", "paper_id": "keep_me", "task": "test", "datasets": [], "metrics": []},
                {"method_card_id": "mc2", "paper_id": "discard_me", "task": "test", "datasets": [], "metrics": []},
            ]
            state.values["extracted_references"] = [
                {"ref_id": "r1", "title": "Ref1", "source_paper_id": "keep_me"},
                {"ref_id": "r2", "title": "Ref2", "source_paper_id": "discard_me"},
            ]

            context = _make_context(tmp)
            agent.run(state, context)

            papers = lit_store.retrieve_papers("test_filter", limit=10)
            self.assertEqual(len(papers), 1)
            self.assertEqual(papers[0]["paper_id"], "keep_me")

            cards = lit_store.retrieve_method_cards("test_filter", limit=10)
            self.assertEqual(len(cards), 1)
            self.assertEqual(cards[0]["paper_id"], "keep_me")

            evidence = lit_store.retrieve_evidence("test_filter", ["keep_me"], limit=10)
            self.assertEqual(len(evidence), 1)
            self.assertEqual(evidence[0]["paper_id"], "keep_me")

    def test_filter_keeps_selected_papers_in_memory(self):
        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            lit_store = LiteratureMemoryStore(db_path)
            agent = LiteratureMemoryPersistenceAgent(lit_memory_store=lit_store)

            topic = _make_topic("test_keep")
            state = ResearchState(topic=topic)
            state.values["selected_papers"] = [
                {
                    "paper_id": "p1",
                    "title": "Paper One",
                    "abstract": "abstract one",
                    "authors": [],
                    "year": 2024,
                    "keywords": [],
                },
                {
                    "paper_id": "p2",
                    "title": "Paper Two",
                    "abstract": "abstract two",
                    "authors": [],
                    "year": 2024,
                    "keywords": [],
                },
            ]
            state.values["parsed_papers"] = {
                "p1": {"paper_id": "p1", "sections": []},
                "p2": {"paper_id": "p2", "sections": []},
            }
            state.values["checked_evidence"] = [
                {"evidence_id": "ev1", "paper_id": "p1", "claim_supported": "yes", "quote": "text", "section": "Abstract", "support_level": "strong"},
                {"evidence_id": "ev2", "paper_id": "p2", "claim_supported": "yes", "quote": "text", "section": "Method", "support_level": "strong"},
            ]
            state.values["method_cards"] = [
                {"method_card_id": "mc1", "paper_id": "p1", "task": "test", "datasets": [], "metrics": []},
                {"method_card_id": "mc2", "paper_id": "p2", "task": "test", "datasets": [], "metrics": []},
            ]

            context = _make_context(tmp)
            agent.run(state, context)

            papers = lit_store.retrieve_papers("test_keep", limit=10)
            self.assertEqual(len(papers), 2)

    def test_filter_filters_extracted_references_by_source_paper_id(self):
        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            lit_store = LiteratureMemoryStore(db_path)
            agent = LiteratureMemoryPersistenceAgent(lit_memory_store=lit_store)

            topic = _make_topic("test_ref")
            state = ResearchState(topic=topic)
            state.values["selected_papers"] = [
                {
                    "paper_id": "keep_me",
                    "title": "Keep",
                    "abstract": "yes",
                    "authors": [],
                    "year": 2024,
                    "keywords": [],
                },
            ]
            state.values["extracted_references"] = [
                {"ref_id": "r1", "title": "Kept Ref", "source_paper_id": "keep_me"},
                {"ref_id": "r2", "title": "Discarded Ref", "source_paper_id": "discard_me"},
            ]

            context = _make_context(tmp)
            agent.run(state, context)

            papers = lit_store.retrieve_papers("test_ref", limit=10)
            self.assertEqual(len(papers), 1)

    def test_filter_no_selected_papers_persists_all(self):
        """When selected_papers is empty (no user selection), persist everything as before."""
        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            lit_store = LiteratureMemoryStore(db_path)
            agent = LiteratureMemoryPersistenceAgent(lit_memory_store=lit_store)

            topic = _make_topic("test_no_filter")
            state = ResearchState(topic=topic)
            state.values["selected_papers"] = []
            state.values["parsed_papers"] = {
                "p1": {"paper_id": "p1", "sections": []},
            }
            state.values["checked_evidence"] = [
                {"evidence_id": "ev1", "paper_id": "p1", "claim_supported": "yes", "quote": "text", "section": "Method", "support_level": "strong"},
            ]
            state.values["method_cards"] = [
                {"method_card_id": "mc1", "paper_id": "p1", "task": "test", "datasets": [], "metrics": []},
            ]

            context = _make_context(tmp)
            agent.run(state, context)

            cards = lit_store.retrieve_method_cards("test_no_filter", limit=10)
            self.assertEqual(len(cards), 1)


if __name__ == "__main__":
    main()
