#!/usr/bin/env python3
import io, json, os, pathlib, tempfile, unittest
from unittest.mock import patch
import motor_tool_gateway as g

class FakeResp(io.BytesIO):
    def __init__(self, data, headers, status=206):
        super().__init__(data); self.headers = headers; self.status = status
    def __enter__(self): return self
    def __exit__(self, *a): self.close()

class Tests(unittest.TestCase):
    def test_split_reassemble(self):
        with tempfile.TemporaryDirectory() as td:
            f = pathlib.Path(td)/"big.bin"; f.write_bytes(os.urandom(300000))
            man = g.split_file(f, pathlib.Path(td)/"parts", 64*1024, "https://x/big.bin")
            self.assertEqual(len(man["parts"]), 5)
            out = pathlib.Path(td)/"back.bin"
            g.reassemble(pathlib.Path(td)/"parts", man, out)
            self.assertEqual(g.sha256_file(out), man["sha256"])

    def test_fetch_resume_range(self):
        import hashlib
        data = os.urandom(250000)
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            (td/"big.bin.partial").write_bytes(data[:100000])
            seen = {}
            def fake_urlopen(req, timeout=None):
                seen["range"] = req.headers.get("Range")
                start = int(seen["range"].split("=")[1].rstrip("-"))
                return FakeResp(data[start:], {"Content-Range": f"bytes {start}-{len(data)-1}/{len(data)}"})
            with patch.object(g, "MIN_INTERVAL", 0), patch("urllib.request.urlopen", fake_urlopen):
                r = g.fetch_resumable("https://x/big.bin", td, part_bytes=64*1024, expected_sha256=hashlib.sha256(data).hexdigest())
            self.assertEqual(seen["range"], "bytes=100000-")
            self.assertEqual(r["verdict"], "VERIFIED_CLOSED")
            self.assertEqual((td/"big.bin").read_bytes(), data)
            self.assertFalse((td/"big.bin.partial").exists())
            self.assertTrue((td/"big.bin.parts"/"manifest.json").is_file())

    def test_args_validator(self):
        with self.assertRaises(RuntimeError): g.validate_args("motores_copy_batches", {"source_dir": "a"})
        with self.assertRaises(RuntimeError): g.validate_args("motores_copy_batches", {"source_dir":"a","dest_dir":"b","batch_size":"25"})
        g.validate_args("motores_copy_batches", {"source_dir":"a","dest_dir":"b","batch_size":25})

    def test_plan_cycle(self):
        plan = {"schema":"yaiwes.tools.workflow.v1","steps":[
            {"id":"a","tool":"motores_copy_batches","needs":["b"]},
            {"id":"b","tool":"motores_copy_batches","needs":["a"]}]}
        with self.assertRaises(RuntimeError): g.validate_plan(plan)

    def test_workflow_done_skip_and_crash_resume(self):
        plan = {"schema":"yaiwes.tools.workflow.v1","steps":[
            {"id":"a","tool":"motores_copy_batches","args":{}},
            {"id":"b","tool":"motores_move_batches","args":{},"needs":["a"]}]}
        calls = []
        def fake(tool, args):
            calls.append(tool); return {"verdict":"VERIFIED_CLOSED"}
        with tempfile.TemporaryDirectory() as td:
            pf = pathlib.Path(td)/"plan.json"; pf.write_text(json.dumps(plan))
            sf = pathlib.Path(td)/"state.json"
            with patch.object(g, "dispatch", fake):
                r1 = g.run_workflow(pf, sf)
                self.assertEqual(r1["verdict"], "VERIFIED_CLOSED")
                r2 = g.run_workflow(pf, sf)
                self.assertEqual(len(calls), 2)
                led = json.loads(sf.read_text()); led["steps"]["b"]["status"] = "RUNNING"; sf.write_text(json.dumps(led))
                led2 = g.load_ledger(plan, sf)
                self.assertEqual(led2["steps"]["b"]["status"], "PENDING")

    def test_workflow_fail_blocked(self):
        plan = {"schema":"yaiwes.tools.workflow.v1","steps":[
            {"id":"a","tool":"motores_copy_batches","args":{},"max_retries":1},
            {"id":"b","tool":"motores_move_batches","args":{},"needs":["a"]}]}
        def fake(tool, args): return {"verdict":"GAPS_PENDING"}
        with tempfile.TemporaryDirectory() as td:
            pf = pathlib.Path(td)/"p.json"; pf.write_text(json.dumps(plan)); sf = pathlib.Path(td)/"s.json"
            with patch.object(g, "dispatch", fake):
                r = g.run_workflow(pf, sf)
            self.assertEqual(r["verdict"], "GAPS_PENDING")
            self.assertEqual(r["steps"], {"a":"FAILED","b":"BLOCKED"})

    def test_retry_wait_headers(self):
        self.assertEqual(g.retry_wait(1, {"Retry-After":"7"}), 7)
        self.assertEqual(g.retry_wait(1), 5); self.assertEqual(g.retry_wait(3), 20)

if __name__ == "__main__": unittest.main()
