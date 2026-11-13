#!/usr/bin/env python3
import json, pathlib, tempfile, unittest
from unittest.mock import patch
import websearch_engine as w

class Tests(unittest.TestCase):
    def test_aggregate(self):
        rows=[
            w.Result("A","https://example.com/x?utm_source=z","one","duckduckgo",1),
            w.Result("A2","https://example.com/x","two longer snippet","brave",2),
            w.Result("B","https://example.org/y","three","tavily",1),
        ]
        m=w.aggregate(rows)
        self.assertEqual(len(m),2)
        self.assertEqual(m[0]["url"],"https://example.com/x")
        self.assertEqual(m[0]["providers"],["brave","duckduckgo"])

    @patch.object(w,"duckduckgo")
    def test_write_and_readback(self,ddg):
        ddg.return_value=[w.Result("Title","https://example.com","Snippet","duckduckgo",1)]
        old=w.FUNCS["duckduckgo"]; w.FUNCS["duckduckgo"]=w.duckduckgo
        try:
            with tempfile.TemporaryDirectory() as td:
                r=w.run("test query",["duckduckgo"],5,pathlib.Path(td))
                self.assertEqual(r["verdict"],"VERIFIED_CLOSED")
                p=json.loads(pathlib.Path(r["result_json"]).read_text())
                self.assertEqual(p["query"],"test query")
                self.assertFalse(p["llm_used"])
                self.assertTrue(pathlib.Path(r["summary_md"]).exists())
        finally: w.FUNCS["duckduckgo"]=old

if __name__=="__main__": unittest.main()
