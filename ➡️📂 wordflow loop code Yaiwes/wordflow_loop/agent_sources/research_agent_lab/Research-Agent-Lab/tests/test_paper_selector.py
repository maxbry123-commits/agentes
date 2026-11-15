from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import patch

from agents.paper_selector import PaperSelectionAgent
from core.agent_base import AgentContext
from core.artifact_store import ArtifactStore
from core.state import ResearchState
from schemas.topic_pack import TopicPack


def _make_state(papers: list[dict]) -> ResearchState:
    topic = TopicPack(topic_name="test_topic")
    state = ResearchState(topic=topic)
    state.values["selected_papers"] = papers
    return state


def _make_context(tmp_path: str) -> AgentContext:
    return AgentContext(
        artifact_store=ArtifactStore(Path(tmp_path)),
        memory_store=None,
        tool_registry=None,
        settings={},
    )


def _sample_papers() -> list[dict]:
    return [
        {
            "paper_id": "p1",
            "title": "Intention-Aware Diffusion Model for Pedestrian Trajectory Prediction",
            "authors": ["Smith, J.", "Jones, K."],
            "year": 2024,
            "relevance_score": 0.92,
            "triage_decision": "read",
            "url": "https://arxiv.org/abs/2401.12345",
            "abstract": "We propose a leapfrog diffusion model for pedestrian trajectory forecasting.",
        },
        {
            "paper_id": "p2",
            "title": "Graph-based Trajectory Prediction",
            "authors": ["Chen, L."],
            "year": 2023,
            "relevance_score": 0.78,
            "triage_decision": "skim",
            "local_path": "/data/papers/graph_traj.pdf",
            "abstract": "A graph-based approach to model interactions between pedestrians.",
        },
        {
            "paper_id": "p3",
            "title": "Language-Conditioned Multi-Agent Forecasting",
            "authors": ["Wang, X.", "Li, Y.", "Zhang, H."],
            "year": 2024,
            "relevance_score": 0.85,
            "triage_decision": "read",
            "url": "",
            "abstract": "We introduce a language-conditioned approach.",
        },
    ]


class PaperSelectionAgentTest(TestCase):
    def test_no_papers_returns_early(self):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state([])
            ctx = _make_context(tmp)
            result = agent.run(state, ctx)
            self.assertIn("no papers to select", result.notes[0])

    @patch("sys.stdin.isatty", return_value=False)
    def test_non_tty_keeps_all_papers(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state(_sample_papers())
            ctx = _make_context(tmp)
            result = agent.run(state, ctx)
            self.assertEqual(len(state.values["selected_papers"]), 3)
            self.assertIn("non-interactive", result.notes[0])

    @patch("sys.stdin.isatty", return_value=True)
    def test_select_by_comma_separated_indices(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state(_sample_papers())
            ctx = _make_context(tmp)
            with patch("builtins.input", return_value="1,3"):
                with patch("sys.stdout", StringIO()):
                    result = agent.run(state, ctx)
            self.assertEqual(len(state.values["selected_papers"]), 2)
            self.assertEqual(state.values["selected_papers"][0]["paper_id"], "p1")
            self.assertEqual(state.values["selected_papers"][1]["paper_id"], "p3")
            self.assertEqual(state.values["selected_paper_count"], 2)

    @patch("sys.stdin.isatty", return_value=True)
    def test_enter_keeps_all_papers(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state(_sample_papers())
            ctx = _make_context(tmp)
            with patch("builtins.input", return_value=""):
                with patch("sys.stdout", StringIO()):
                    result = agent.run(state, ctx)
            self.assertEqual(len(state.values["selected_papers"]), 3)
            self.assertEqual(state.values["selected_paper_count"], 3)

    @patch("sys.stdin.isatty", return_value=True)
    def test_none_clears_all_papers(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state(_sample_papers())
            ctx = _make_context(tmp)
            with patch("builtins.input", return_value="none"):
                with patch("sys.stdout", StringIO()):
                    result = agent.run(state, ctx)
            self.assertEqual(len(state.values["selected_papers"]), 0)
            self.assertEqual(state.values["selected_paper_count"], 0)

    @patch("sys.stdin.isatty", return_value=True)
    def test_display_includes_relevance_score_and_decision(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state([_sample_papers()[0]])
            ctx = _make_context(tmp)
            buf = StringIO()
            with patch("builtins.input", return_value="1"):
                with patch("sys.stdout", buf):
                    agent.run(state, ctx)
            output = buf.getvalue()
            self.assertIn("★0.92 read", output)
            self.assertIn("Intention-Aware", output)
            self.assertIn("Smith, J., Jones, K.", output)
            self.assertIn("2024", output)

    @patch("sys.stdin.isatty", return_value=True)
    def test_display_shows_url_when_present(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state([_sample_papers()[0]])
            ctx = _make_context(tmp)
            buf = StringIO()
            with patch("builtins.input", return_value="1"):
                with patch("sys.stdout", buf):
                    agent.run(state, ctx)
            output = buf.getvalue()
            self.assertIn("https://arxiv.org/abs/2401.12345", output)

    @patch("sys.stdin.isatty", return_value=True)
    def test_display_shows_local_path_when_no_url(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state([_sample_papers()[1]])
            ctx = _make_context(tmp)
            buf = StringIO()
            with patch("builtins.input", return_value="1"):
                with patch("sys.stdout", buf):
                    agent.run(state, ctx)
            output = buf.getvalue()
            self.assertIn("/data/papers/graph_traj.pdf", output)

    @patch("sys.stdin.isatty", return_value=True)
    def test_display_shows_pdf_path_fallback(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            papers = [{
                "paper_id": "p4",
                "title": "Test Paper",
                "authors": "Author",
                "year": 2024,
                "relevance_score": 0.5,
                "triage_decision": "skim",
                "pdf_path": "/data/test.pdf",
                "abstract": "Test abstract.",
            }]
            state = _make_state(papers)
            ctx = _make_context(tmp)
            buf = StringIO()
            with patch("builtins.input", return_value="1"):
                with patch("sys.stdout", buf):
                    agent.run(state, ctx)
            output = buf.getvalue()
            self.assertIn("/data/test.pdf", output)

    @patch("sys.stdin.isatty", return_value=True)
    def test_authors_list_joined_with_comma(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state([_sample_papers()[2]])
            ctx = _make_context(tmp)
            buf = StringIO()
            with patch("builtins.input", return_value="1"):
                with patch("sys.stdout", buf):
                    agent.run(state, ctx)
            output = buf.getvalue()
            self.assertIn("Wang, X., Li, Y., Zhang, H.", output)

    @patch("sys.stdin.isatty", return_value=True)
    def test_invalid_input_indices_ignored(self, _mock_isatty):
        with TemporaryDirectory() as tmp:
            agent = PaperSelectionAgent()
            state = _make_state(_sample_papers())
            ctx = _make_context(tmp)
            with patch("builtins.input", return_value="1,abc,5"):
                with patch("sys.stdout", StringIO()):
                    result = agent.run(state, ctx)
            self.assertEqual(len(state.values["selected_papers"]), 1)
            self.assertEqual(state.values["selected_papers"][0]["paper_id"], "p1")


if __name__ == "__main__":
    main()
