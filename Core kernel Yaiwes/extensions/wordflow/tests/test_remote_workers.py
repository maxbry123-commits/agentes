# -*- coding: utf-8 -*-
"""Tests D5 remote workers."""
from __future__ import annotations

import unittest

from extensions.wordflow.engine.remote_workers import RemoteWorkerRouter


class TestRemoteWorkers(unittest.TestCase):
    def test_local(self):
        r = RemoteWorkerRouter().route("t1", mode="local")
        self.assertTrue(r["ok"])

    def test_ssh_fake(self):
        r = RemoteWorkerRouter().route("t2", mode="ssh", host="vps1", command="echo ok")
        self.assertTrue(r["ok"])
        self.assertEqual(r["mode"], "ssh")

    def test_docker_fake(self):
        r = RemoteWorkerRouter().route("t3", mode="docker", command="python -V")
        self.assertTrue(r["ok"])
        self.assertEqual(r["mode"], "docker")

    def test_real_forbidden(self):
        with self.assertRaises(RuntimeError):
            RemoteWorkerRouter(allow_real=True)


if __name__ == "__main__":
    unittest.main()
