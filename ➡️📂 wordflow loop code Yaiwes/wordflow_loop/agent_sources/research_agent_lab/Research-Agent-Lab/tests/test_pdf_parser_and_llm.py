from __future__ import annotations

from dataclasses import asdict
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

from schemas.paper import Paper
from tools.local_pdf_parser import LocalPdfParser
from tools.llm_client import OpenAICompatibleClient, extract_json_object
from tools.model_router import ModelRoute


class PdfParserAndLLMTest(unittest.TestCase):
    def test_pdf_parser_reports_missing_parser_or_parse_result(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "paper.pdf"
            path.write_bytes(b"%PDF-1.4\n% minimal placeholder\n")
            paper = Paper(title="paper", local_path=str(path), pdf_path=str(path))

            old_stderr = sys.stderr
            sys.stderr = open(os.devnull, "w")
            try:
                parsed = LocalPdfParser().parse(asdict(paper))
            finally:
                sys.stderr.close()
                sys.stderr = old_stderr

            self.assertIn(parsed.status, {"parser_missing", "parse_error", "empty_text", "parsed"})

    def test_llm_client_refuses_disabled_route_without_key(self) -> None:
        old = os.environ.pop("DEEPSEEK_API_KEY", None)
        try:
            route = ModelRoute(
                agent="reviewer_agent",
                provider="deepseek",
                model="deepseek-v4-pro",
                api_key_env="DEEPSEEK_API_KEY",
                enabled=False,
            )
            response = OpenAICompatibleClient().chat(route, [{"role": "user", "content": "hi"}])

            self.assertFalse(response.ok)
            self.assertIn("disabled", response.error)
        finally:
            if old is not None:
                os.environ["DEEPSEEK_API_KEY"] = old

    def test_extract_json_object_from_model_text(self) -> None:
        payload = extract_json_object('notes\n```json\n{"task": "forecast", "metrics": ["ADE"]}\n```')

        self.assertEqual(payload, {"task": "forecast", "metrics": ["ADE"]})


class MultiSectionEvidenceTest(unittest.TestCase):
    def test_multi_section_evidence_selects_best_chunks(self):
        from agents.paper_reader import _select_evidence_chunks

        chunks = [
            {"text": "abstract text", "section": "Abstract", "chunk_id": "p1:0"},
            {"text": "intro text", "section": "Introduction", "chunk_id": "p1:1"},
            {"text": "method text", "section": "Method", "chunk_id": "p1:2"},
            {"text": "experiment text", "section": "Experiments", "chunk_id": "p1:3"},
            {"text": "extra method detail", "section": "Method", "chunk_id": "p1:4"},
        ]
        paper = {"paper_id": "p1", "keywords": ["trajectory", "prediction"]}

        selected = _select_evidence_chunks(chunks, "p1", paper)
        self.assertGreaterEqual(len(selected), 1)
        self.assertLessEqual(len(selected), 3)
        sections = [c["section"] for c in selected]
        self.assertIn("Abstract", sections)
        self.assertIn("Method", sections)

    def test_multi_section_evidence_fallback_single_chunk(self):
        from agents.paper_reader import _select_evidence_chunks

        chunks = [
            {"text": "some text without clear section", "section": "Unknown", "chunk_id": "p2:0"},
        ]
        paper = {"paper_id": "p2", "keywords": []}
        selected = _select_evidence_chunks(chunks, "p2", paper)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["chunk_id"], "p2:0")

    def test_multi_section_evidence_fallback_abstract_from_paper_dict(self):
        from agents.paper_reader import _select_evidence_chunks

        paper = {"paper_id": "p3", "abstract": "This is the paper abstract.", "keywords": []}
        selected = _select_evidence_chunks([], "p3", paper)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["text"], "This is the paper abstract.")
        self.assertEqual(selected[0]["section"], "Abstract")

    def test_multi_section_evidence_empty_input(self):
        from agents.paper_reader import _select_evidence_chunks

        paper = {"paper_id": "p4", "keywords": []}
        selected = _select_evidence_chunks([], "p4", paper)
        self.assertEqual(len(selected), 0)

    def test_multi_section_evidence_architecture_label(self):
        from agents.paper_reader import _select_evidence_chunks

        chunks = [
            {"text": "abstract here", "section": "Abstract", "chunk_id": "p5:a"},
            {"text": "model details", "section": "Model Architecture", "chunk_id": "p5:m"},
            {"text": "results here", "section": "Results", "chunk_id": "p5:r"},
        ]
        paper = {"paper_id": "p5", "keywords": []}
        selected = _select_evidence_chunks(chunks, "p5", paper)
        self.assertGreaterEqual(len(selected), 2)
        section_names = [c["section"] for c in selected]
        self.assertIn("Abstract", section_names)
        self.assertIn("Model Architecture", section_names)


if __name__ == "__main__":
    unittest.main()
