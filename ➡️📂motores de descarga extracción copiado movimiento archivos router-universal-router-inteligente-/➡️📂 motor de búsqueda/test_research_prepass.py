#!/usr/bin/env python3
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import research_prepass as r


class ResearchPrepassTests(unittest.TestCase):
    def test_query_is_deterministic(self):
        text = "INPUT BLOCK: integra FastAPI router_modelos.py con ErrorCode42 y GitHub."
        q1, t1 = r.build_query(text)
        q2, t2 = r.build_query(text)
        self.assertEqual(q1, q2)
        self.assertEqual(t1, t2)
        self.assertIn("router_modelos.py", q1)
        self.assertIn("ErrorCode42", q1)

    def test_domain_filter(self):
        self.assertTrue(r.hostname_matches("https://docs.python.org/3/library/json.html", "docs.python.org"))
        self.assertFalse(r.hostname_matches("https://example.com/docs.python.org/x", "docs.python.org"))
        self.assertTrue(r.hostname_matches("https://vercel.com/docs/functions", "vercel.com", "/docs"))
        self.assertFalse(r.hostname_matches("https://vercel.com/blog/x", "vercel.com", "/docs"))

    def test_budget_and_dedupe(self):
        rows = [
            {"source_id":"github","source_kind":"code","source_weight":1.0,"title":"A","url":"https://github.com/a/a","snippet":"FastAPI router","rank":1,"provider":"github_api"},
            {"source_id":"github","source_kind":"code","source_weight":1.0,"title":"A2","url":"https://github.com/a/a","snippet":"duplicate","rank":2,"provider":"github_api"},
            {"source_id":"python_docs","source_kind":"official_docs","source_weight":0.94,"title":"B","url":"https://docs.python.org/x","snippet":"FastAPI related docs","rank":1,"provider":"ddgs"},
        ]
        ranked = r.rank_records(rows, ["FastAPI"])
        self.assertEqual(len(ranked), 2)
        selected, used, truncated = r.select_budget(ranked, 500, 2)
        self.assertEqual(len(selected), 2)
        self.assertGreater(used, 0)
        self.assertFalse(truncated)

    def test_verbatim_and_no_llm(self):
        registry = r.DEFAULT_REGISTRY
        source = json.loads(registry.read_text())
        fake = lambda s, q, limit: [
            r.make_record(s, "Title "+s["id"], "https://example.com/"+s["id"], "evidence "+q[:40], 1, "mock")
        ]

        def fake_web(s, q, limit):
            domain = s["domain"]
            path = s.get("path_prefix", "") or "/x"
            return [r.make_record(s, "Title "+s["id"], "https://"+domain+path, "evidence", 1, "mock")]

        with tempfile.TemporaryDirectory() as td:
            with patch.object(r, "github_search", side_effect=fake), patch.object(r, "hf_search", side_effect=fake), patch.object(r, "search_web_source", side_effect=fake_web):
                raw = "LINEA 1\nLINEA 2 exacta\n"
                packet = r.run(
                    input_text=raw,
                    input_origin="test",
                    plan_text="",
                    plan_origin="",
                    registry_path=registry,
                    output_root=pathlib.Path(td),
                    limit=2,
                    budget_tokens=5000,
                    max_per_source=2,
                    cache_ttl=0,
                    force=True,
                )
                self.assertFalse(packet["llm_used"])
                self.assertTrue(packet["input"]["verbatim_preserved"])
                self.assertEqual(pathlib.Path(packet["input"]["path"]).read_text(), raw)
                self.assertEqual(len(packet["sources_requested"]), len(source["direct_sources"]) + len(source["web_sources"]))
                self.assertTrue(pathlib.Path(packet["context_packet"]).is_file())
                self.assertTrue(pathlib.Path(packet["context_md"]).is_file())


if __name__ == "__main__":
    unittest.main()
