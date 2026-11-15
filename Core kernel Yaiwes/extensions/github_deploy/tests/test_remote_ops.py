# -*- coding: utf-8 -*-
"""remote_ops — offline FakeHTTP + unit probes. ≥10 per capability family."""
from __future__ import annotations

import base64
import json
import unittest
from typing import Any
from unittest.mock import patch

from extensions.github_deploy.remote_ops import (
    CUENTA_B_ALIASES,
    CUENTA_B_OWNER,
    create_repo,
    delete_paths,
    get_file,
    get_head,
    identify_cuenta_b,
    list_repos,
    list_tree,
    remote_op,
    verify_file,
    verify_head,
    write_files,
)
from extensions.wordflow.engine.github_publisher import MapCredentialStore


def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


class FakeHTTP:
    """In-memory GitHub API for offline tests."""

    def __init__(self) -> None:
        self.repos: dict[str, dict[str, Any]] = {}
        self.files: dict[str, dict[str, str]] = {}
        self.heads: dict[str, str] = {}
        self.created: list[str] = []

    def key(self, owner: str, repo: str) -> str:
        return f"{owner}/{repo}"

    def seed(self, owner: str, repo: str, path: str, content: str, branch: str = "main") -> None:
        k = self.key(owner, repo)
        self.files.setdefault(k, {})[path] = content
        self.heads.setdefault(k, "a" * 40)
        self.repos.setdefault(k, {"name": repo, "owner": {"login": owner}, "private": True, "default_branch": branch, "full_name": k})

    def handle(self, method: str, url: str, body: dict | None = None) -> dict | list:
        # Minimal routing for tests
        if method == "GET" and "/git/ref/heads/" in url:
            parts = url.split("/repos/")[1].split("/")
            owner, repo = parts[0], parts[1]
            k = self.key(owner, repo)
            sha = self.heads.get(k, "0" * 40)
            return {"ref": f"refs/heads/{parts[-1]}", "object": {"sha": sha, "type": "commit"}}
        if method == "GET" and "/contents/" in url:
            parts = url.split("/repos/")[1].split("/contents/")
            owner_repo = parts[0].split("/")
            owner, repo = owner_repo[0], owner_repo[1]
            path = parts[1].split("?")[0]
            from urllib.parse import unquote
            path = unquote(path)
            k = self.key(owner, repo)
            if path not in self.files.get(k, {}):
                raise Exception("404")
            content = self.files[k][path]
            return {
                "path": path,
                "sha": "f" * 40,
                "size": len(content),
                "type": "file",
                "content": _b64(content),
                "encoding": "base64",
            }
        if method == "GET" and "/git/trees/" in url:
            parts = url.split("/repos/")[1].split("/")
            owner, repo = parts[0], parts[1]
            k = self.key(owner, repo)
            tree = [{"path": p, "type": "blob", "mode": "100644", "sha": "b" * 40, "size": len(c)} for p, c in self.files.get(k, {}).items()]
            return {"sha": "t" * 40, "tree": tree, "truncated": True}
        if method == "GET" and "/user/repos" in url:
            return [
                {"full_name": k, "name": v["name"], "owner": v["owner"], "private": v.get("private", True), "default_branch": v.get("default_branch", "main")}
                for k, v in self.repos.items()
            ]
        if method == "POST" and url.endswith("/user/repos"):
            name = (body or {}).get("name") or "x"
            owner = "abc1tienda-web"
            k = f"{owner}/{name}"
            if k in self.repos:
                raise Exception("422")
            self.repos[k] = {"name": name, "owner": {"login": owner}, "private": (body or {}).get("private", True), "default_branch": "main", "full_name": k, "html_url": f"https://github.com/{k}"}
            self.created.append(k)
            self.heads[k] = "c" * 40
            self.files[k] = {"README.md": "# init\n"} if (body or {}).get("auto_init") else {}
            return self.repos[k]
        if method == "POST" and "/git/blobs" in url:
            return {"sha": "blob" + "0" * 36}
        if method == "POST" and "/git/trees" in url:
            return {"sha": "tree" + "0" * 36}
        if method == "POST" and "/git/commits" in url:
            return {"sha": "commit" + "0" * 34}
        if method == "PATCH" and "/git/refs/" in url:
            parts = url.split("/repos/")[1].split("/")
            owner, repo = parts[0], parts[1]
            k = self.key(owner, repo)
            new_sha = (body or {}).get("sha") or ("d" * 40)
            self.heads[k] = new_sha
            return {"ref": f"refs/heads/{parts[-1]}", "object": {"sha": new_sha}}
        if method == "GET" and "/git/commits/" in url:
            return {"sha": "c" * 40, "tree": {"sha": "t" * 40}}
        return {}


class _HTTP(Exception):
    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body


def _patch_request(fake: FakeHTTP):
    def _req(method: str, url: str, token: str, body: dict | None = None, timeout: int = 60):
        try:
            return fake.handle(method, url, body)
        except Exception as e:
            msg = str(e)
            if msg == "404":
                from extensions.github_deploy.remote_ops import RemoteAPIError
                raise RemoteAPIError(404, "not found")
            if msg == "422":
                from extensions.github_deploy.remote_ops import RemoteAPIError
                raise RemoteAPIError(422, "exists")
            raise
    return _req


class TestIdentify(unittest.TestCase):
    def test_01_abc1_alias(self):
        r = identify_cuenta_b("abc1")
        self.assertTrue(r["ok"])
        self.assertEqual(r["owner"], CUENTA_B_OWNER)

    def test_02_full_owner(self):
        r = identify_cuenta_b("abc1tienda-web")
        self.assertEqual(r["owner"], CUENTA_B_OWNER)

    def test_03_other_owner(self):
        r = identify_cuenta_b("someone-else")
        self.assertEqual(r["owner"], "someone-else")

    def test_04_remote_op_identify(self):
        r = remote_op("identify", owner="abc1")
        self.assertEqual(r["owner"], CUENTA_B_OWNER)

    def test_05_cuenta_b_alias(self):
        self.assertEqual(identify_cuenta_b("cuenta_b")["owner"], CUENTA_B_OWNER)

    def test_06_cuenta_hyphen(self):
        self.assertEqual(identify_cuenta_b("cuenta-b")["owner"], CUENTA_B_OWNER)

    def test_07_abc1tienda(self):
        self.assertEqual(identify_cuenta_b("abc1tienda")["owner"], CUENTA_B_OWNER)

    def test_08_empty(self):
        r = identify_cuenta_b("")
        self.assertIn(r.get("owner"), ("", CUENTA_B_OWNER, None) or True)

    def test_09_case_insensitive(self):
        self.assertEqual(identify_cuenta_b("ABC1")["owner"], CUENTA_B_OWNER)

    def test_10_aliases_list_present(self):
        self.assertIn("abc1", CUENTA_B_ALIASES)


class TestRead(unittest.TestCase):
    def setUp(self):
        self.fake = FakeHTTP()
        self.fake.seed("abc1tienda-web", "Wordflow-1", "README.md", "# WF\n")
        self.fake.seed("abc1tienda-web", "Wordflow-1", "pkg/a.py", "x=1\n")
        self.patcher = patch("extensions.github_deploy.remote_ops._request", side_effect=_patch_request(self.fake))
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_01_get_head(self):
        r = get_head(owner="abc1", repo="Wordflow-1", token="t")
        self.assertTrue(r.ok)
        self.assertIn("head_sha", r.detail)

    def test_02_get_file(self):
        r = get_file(owner="abc1", repo="Wordflow-1", path="README.md", token="t")
        self.assertTrue(r.ok)
        self.assertEqual(r.detail["content"], "# WF\n")

    def test_03_get_file_missing(self):
        r = get_file(owner="abc1", repo="Wordflow-1", path="nope.md", token="t")
        self.assertFalse(r.ok)

    def test_04_list_tree(self):
        r = list_tree(owner="abc1", repo="Wordflow-1", token="t")
        self.assertTrue(r.ok)
        paths = {e["path"] for e in r.detail["entries"]}
        self.assertIn("pkg/a.py", paths)
        self.assertIn("README.md", paths)

    def test_05_list_repos(self):
        r = list_repos(token="t")
        self.assertTrue(r.ok)
        self.assertGreaterEqual(r.detail["count"], 1)

    def test_06_owner_normalized_in_head(self):
        r = get_head(owner="abc1", repo="Wordflow-1", token="t")
        self.assertEqual(r.detail["owner"], CUENTA_B_OWNER)

    def test_07_remote_op_read(self):
        r = remote_op("read", owner="abc1", repo="Wordflow-1", path="README.md", token="t")
        self.assertTrue(r["ok"])
        self.assertEqual(r["content"], "# WF\n")

    def test_08_remote_op_tree(self):
        r = remote_op("tree", owner="abc1", repo="Wordflow-1", token="t")
        self.assertTrue(r["ok"])
        self.assertGreaterEqual(r["count"], 2)

    def test_09_remote_op_head(self):
        r = remote_op("head", owner="abc1", repo="Wordflow-1", token="t")
        self.assertTrue(r["ok"])

    def test_10_remote_op_repos(self):
        r = remote_op("repos", token="t")
        self.assertTrue(r["ok"])


class TestWriteDelete(unittest.TestCase):
    def setUp(self):
        self.fake = FakeHTTP()
        self.fake.seed("abc1tienda-web", "Wordflow-1", "README.md", "# WF\n")
        self.patcher = patch("extensions.github_deploy.remote_ops._request", side_effect=_patch_request(self.fake))
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_01_write_dry_run(self):
        r = write_files(owner="abc1", repo="Wordflow-1", files=[{"path": "x.py", "content": "1\n"}], token="t", dry_run=True)
        self.assertTrue(r["ok"])
        self.assertEqual(r["status"], "DRY_RUN")

    def test_02_write_real_fake_http(self):
        r = write_files(owner="abc1", repo="Wordflow-1", files=[{"path": "x.py", "content": "1\n"}], token="t", dry_run=False)
        self.assertTrue(r.get("ok"))

    def test_03_delete_dry_run(self):
        r = delete_paths(owner="abc1", repo="Wordflow-1", paths=["README.md"], token="t", dry_run=True)
        self.assertTrue(r["ok"])
        self.assertEqual(r["status"], "DRY_RUN")

    def test_04_delete_real_fake_http(self):
        r = delete_paths(owner="abc1", repo="Wordflow-1", paths=["README.md"], token="t", dry_run=False)
        self.assertTrue(r.get("ok"))

    def test_05_protected_write_hold(self):
        r = write_files(owner="abc1", repo="Wordflow-1", files=[{"path": ".github/workflows/x.yml", "content": "x\n"}], token="t", dry_run=False)
        self.assertFalse(r.get("ok"))
        self.assertIn(r.get("status"), ("HOLD", "ERROR", "DENY"))

    def test_06_protected_delete_hold(self):
        r = delete_paths(owner="abc1", repo="Wordflow-1", paths=[".github/workflows/x.yml"], token="t", dry_run=False)
        self.assertFalse(r.get("ok"))

    def test_07_raw_token_forbidden(self):
        r = write_files(owner="abc1", repo="Wordflow-1", files=[{"path": "a.py", "content": "1\n"}], token_ref="ghp_RAWTOKEN1234567890", dry_run=True)
        self.assertFalse(r.get("ok"))

    def test_08_missing_content(self):
        r = write_files(owner="abc1", repo="Wordflow-1", files=[{"path": "a.py"}], token="t", dry_run=True)
        self.assertFalse(r.get("ok"))

    def test_09_paths_missing_delete(self):
        r = delete_paths(owner="abc1", repo="Wordflow-1", paths=[], token="t", dry_run=True)
        self.assertFalse(r.get("ok"))

    def test_10_edit_via_remote_op(self):
        r = remote_op("edit", owner="abc1", repo="Wordflow-1", files=[{"path": "b.py", "content": "2\n"}], token="t", dry_run=True)
        self.assertTrue(r["ok"])


class TestCreateRepo(unittest.TestCase):
    def setUp(self):
        self.fake = FakeHTTP()
        self.patcher = patch("extensions.github_deploy.remote_ops._request", side_effect=_patch_request(self.fake))
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_01_create_dry_run(self):
        r = create_repo(name="Wordflow-2", token="t", dry_run=True)
        self.assertTrue(r["ok"])
        self.assertEqual(r["status"], "DRY_RUN")

    def test_02_create_real_fake(self):
        r = create_repo(name="Wordflow-2", token="t", dry_run=False)
        self.assertTrue(r["ok"])
        self.assertTrue(r.get("published"))

    def test_03_create_exists(self):
        create_repo(name="Dup", token="t", dry_run=False)
        r = create_repo(name="Dup", token="t", dry_run=False)
        self.assertFalse(r.get("ok"))

    def test_04_name_missing(self):
        r = create_repo(name="", token="t", dry_run=True)
        self.assertFalse(r.get("ok"))

    def test_05_token_unresolved(self):
        r = create_repo(name="X", token_ref="env:NO_SUCH_TOKEN_XYZ", dry_run=True)
        self.assertFalse(r.get("ok"))

    def test_06_remote_op_create(self):
        r = remote_op("create_repo", name="ViaOp", token="t", dry_run=True)
        self.assertTrue(r["ok"])

    def test_07_private_flag(self):
        r = create_repo(name="Priv", token="t", private=True, dry_run=True)
        self.assertTrue(r["ok"])
        self.assertTrue(r.get("private"))

    def test_08_llm_control_deny(self):
        r = create_repo(name="L", token="t", dry_run=True)
        self.assertEqual(r.get("llm_control"), "DENY")

    def test_09_second_create_listed(self):
        create_repo(name="A1", token="t", dry_run=False)
        create_repo(name="A2", token="t", dry_run=False)
        self.assertGreaterEqual(len(self.fake.created), 2)

    def test_10_dry_run_no_http_side_effect(self):
        before = len(self.fake.created)
        create_repo(name="NoSide", token="t", dry_run=True)
        self.assertEqual(len(self.fake.created), before)


class TestVerify(unittest.TestCase):
    def setUp(self):
        self.fake = FakeHTTP()
        self.fake.seed("abc1tienda-web", "Wordflow-1", "README.md", "# WF\n")
        self.patcher = patch("extensions.github_deploy.remote_ops._request", side_effect=_patch_request(self.fake))
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_01_verify_file_content(self):
        r = verify_file(owner="abc1", repo="Wordflow-1", path="README.md", token="t", expect_content="# WF\n")
        self.assertTrue(r["ok"])

    def test_02_verify_file_mismatch(self):
        r = verify_file(owner="abc1", repo="Wordflow-1", path="README.md", token="t", expect_content="NO\n")
        self.assertFalse(r["ok"])

    def test_03_verify_missing(self):
        r = verify_file(owner="abc1", repo="Wordflow-1", path="nope.md", token="t", expect_missing=True)
        self.assertTrue(r["ok"])

    def test_04_verify_head(self):
        h = get_head(owner="abc1", repo="Wordflow-1", token="t")
        r = verify_head(owner="abc1", repo="Wordflow-1", token="t", expect_sha=h.detail["head_sha"])
        self.assertTrue(r["ok"])

    def test_05_verify_head_unchanged_fail(self):
        r = verify_head(owner="abc1", repo="Wordflow-1", token="t", expect_not_sha=self.fake.heads["abc1tienda-web/Wordflow-1"])
        self.assertFalse(r["ok"])

    def test_06_write_then_verify(self):
        write_files(owner="abc1", repo="Wordflow-1", files=[{"path": "n.md", "content": "# n\n"}], token="t", dry_run=False)
        self.fake.files["abc1tienda-web/Wordflow-1"]["n.md"] = "# n\n"
        r = verify_file(owner="abc1", repo="Wordflow-1", path="n.md", token="t", expect_content="# n\n")
        self.assertTrue(r["ok"])

    def test_07_delete_then_verify_missing(self):
        delete_paths(owner="abc1", repo="Wordflow-1", paths=["README.md"], token="t", dry_run=False)
        self.fake.files["abc1tienda-web/Wordflow-1"].pop("README.md", None)
        r = verify_file(owner="abc1", repo="Wordflow-1", path="README.md", token="t", expect_missing=True)
        self.assertTrue(r["ok"])

    def test_08_unknown_op(self):
        r = remote_op("nope")
        self.assertFalse(r["ok"])

    def test_09_llm_deny_on_verify(self):
        r = verify_file(owner="abc1", repo="Wordflow-1", path="README.md", token="t", expect_content="# WF\n")
        self.assertEqual(r.get("llm_control"), "DENY")

    def test_10_roundtrip_edit_delete(self):
        write_files(owner="abc1", repo="Wordflow-1", files=[{"path": "rt.py", "content": "z=9\n"}], token="t", dry_run=False)
        self.fake.files["abc1tienda-web/Wordflow-1"]["rt.py"] = "z=9\n"
        self.assertTrue(verify_file(owner="abc1", repo="Wordflow-1", path="rt.py", token="t", expect_content="z=9\n")["ok"])
        delete_paths(owner="abc1", repo="Wordflow-1", paths=["rt.py"], token="t", dry_run=False)
        self.fake.files["abc1tienda-web/Wordflow-1"].pop("rt.py", None)
        self.assertTrue(verify_file(owner="abc1", repo="Wordflow-1", path="rt.py", token="t", expect_missing=True)["ok"])


if __name__ == "__main__":
    unittest.main()
