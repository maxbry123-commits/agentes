from __future__ import annotations

from unittest import TestCase, main

from tools.local_pdf_parser import detect_sections, _section_at


class SectionDetectionTest(TestCase):
    def test_detects_standard_sections(self):
        text = (
            "Abstract\n"
            "This paper proposes a new method.\n\n"
            "1. Introduction\n"
            "Trajectory prediction is important.\n\n"
            "2. Related Work\n"
            "Previous methods use RNNs.\n\n"
            "3. Method\n"
            "We propose a diffusion-based model.\n\n"
            "4. Experiments\n"
            "We evaluate on VIRAT dataset.\n\n"
            "5. Conclusion\n"
            "Our method outperforms baselines.\n\n"
            "References\n"
            "[1] Some paper.\n"
        )
        boundaries = detect_sections(text)
        labels = [_section_at(pos, boundaries) for pos in [5, 55, 110, 150, 210, 260, 310]]
        self.assertEqual(labels[0], "Abstract")
        self.assertEqual(labels[1], "Introduction")
        self.assertEqual(labels[2], "Related Work")
        self.assertEqual(labels[3], "Method")
        self.assertEqual(labels[4], "Experiments")
        self.assertEqual(labels[5], "Conclusion")
        self.assertEqual(labels[6], "References")

    def test_section_at_returns_previous_section(self):
        boundaries = [(0, "Abstract"), (100, "Method"), (300, "Experiments")]
        self.assertEqual(_section_at(0, boundaries), "Abstract")
        self.assertEqual(_section_at(50, boundaries), "Abstract")
        self.assertEqual(_section_at(100, boundaries), "Method")
        self.assertEqual(_section_at(250, boundaries), "Method")
        self.assertEqual(_section_at(500, boundaries), "Experiments")

    def test_return_unknown_before_first_section(self):
        boundaries = [(50, "Abstract"), (200, "Method")]
        self.assertEqual(_section_at(10, boundaries), "Unknown")

    def test_no_duplicate_positions(self):
        text = (
            "1. Introduction\nSome text.\n\n"
            "Introduction\nMore text.\n\n"
            "3. Method\nMethod description.\n"
        )
        boundaries = detect_sections(text)
        labels = {label for _, label in boundaries}
        self.assertIn("Introduction", labels)
        self.assertIn("Method", labels)

    def test_empty_text(self):
        boundaries = detect_sections("")
        self.assertEqual(boundaries, [])

    def test_variations(self):
        text = (
            "ABSTRACT\nabstract content\n\n"
            "I. INTRODUCTION\nintro content\n\n"
            "RELATED WORK\nrelated content\n\n"
            "PROPOSED METHOD\nmethod content\n\n"
            "EXPERIMENTS\nexp content\n\n"
            "CONCLUSION AND LIMITATIONS\nconc content\n"
        )
        boundaries = detect_sections(text)
        labels = {label for _, label in boundaries}
        self.assertIn("Abstract", labels)
        self.assertIn("Introduction", labels)
        self.assertIn("Related Work", labels)
        self.assertIn("Method", labels)
        self.assertIn("Experiments", labels)
        self.assertIn("Conclusion", labels)

    def test_numbered_subsections(self):
        text = (
            "3. Method\n"
            "3.1 Encoder Architecture\n"
            "encoder details\n"
            "3.2 Decoder Architecture\n"
            "decoder details\n"
        )
        boundaries = detect_sections(text)
        labels = [label for _, label in boundaries]
        self.assertIn("Method", labels)


class SectionChunkingTest(TestCase):
    def test_chunks_at_section_boundaries(self):
        from tools.local_pdf_parser import LocalPdfParser

        text = (
            "Abstract\nThis paper proposes a method.\n\n"
            "1. Introduction\nTrajectory prediction is important for autonomous driving.\n\n"
            "2. Related Work\nPrevious methods use RNNs and GNNs.\n\n"
            "3. Method\nWe propose a diffusion-based model for predicting trajectories.\nOur model uses a denoising diffusion process with social context.\n\n"
            "4. Experiments\nWe evaluate on VIRAT and ETH/UCY datasets.\nOur method achieves state-of-the-art results.\n\n"
            "5. Conclusion\nWe presented a novel trajectory prediction method.\n\n"
            "References\n[1] Some paper title. In CVPR 2023.\n[2] Another paper. In NeurIPS 2022.\n"
        )
        boundaries = detect_sections(text)
        parser = LocalPdfParser()
        chunks = parser._chunks("paper_1", text, boundaries)

        self.assertGreater(len(chunks), 1)
        sections = {chunk.section for chunk in chunks}
        self.assertIn("Abstract", sections)
        self.assertIn("Introduction", sections)
        self.assertIn("Method", sections)

    def test_chunks_fallback_without_boundaries(self):
        from tools.local_pdf_parser import LocalPdfParser

        text = "This is a plain text without any section headers.\n" * 50
        parser = LocalPdfParser(chunk_chars=200)
        chunks = parser._chunks("paper_2", text, [])

        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertEqual(chunk.section, "Unknown")
            self.assertLessEqual(len(chunk.text), 200)

    def test_empty_text_returns_empty_chunks(self):
        from tools.local_pdf_parser import LocalPdfParser

        parser = LocalPdfParser()
        chunks = parser._chunks("paper_3", "", [])
        self.assertEqual(chunks, [])

        chunks_with_boundaries = parser._chunks("paper_4", "", [(0, "Abstract")])
        self.assertEqual(chunks_with_boundaries, [])

    def test_long_section_split_at_paragraphs(self):
        from tools.local_pdf_parser import LocalPdfParser

        paragraphs = ["Paragraph " + str(i) + ". " + "x" * 100 for i in range(20)]
        text = "1. Introduction\n" + "\n\n".join(paragraphs)
        boundaries = detect_sections(text)
        parser = LocalPdfParser(chunk_chars=200)
        chunks = parser._chunks("paper_5", text, boundaries)

        intro_chunks = [c for c in chunks if c.section == "Introduction"]
        self.assertGreater(len(intro_chunks), 1)
        for chunk in intro_chunks:
            self.assertLessEqual(len(chunk.text), 200)

    def test_chunks_preserves_sections_with_leading_whitespace(self):
        """Bug 1 regression: leading whitespace should not corrupt section text."""
        from tools.local_pdf_parser import LocalPdfParser

        text = "  \nAbstract\nThis is the abstract.\n\n1. Introduction\nThis is intro.\n\nReferences\n[1] Paper.\n  "
        boundaries = detect_sections(text)
        parser = LocalPdfParser()
        chunks = parser._chunks("paper_6", text, boundaries)

        abstract_chunks = [c for c in chunks if c.section == "Abstract"]
        self.assertGreaterEqual(len(abstract_chunks), 1)
        self.assertTrue(
            abstract_chunks[0].text.startswith("Abstract"),
            f"Abstract text corrupted, starts with: {repr(abstract_chunks[0].text[:30])}",
        )


if __name__ == "__main__":
    main()
