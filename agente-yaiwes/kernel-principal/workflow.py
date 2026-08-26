"""WordflowKernel orchestrator — audit → gaps → tasks.

Default inject: ForensicEngine + GapTaskCompiler (no LLM).
Pass auto_inject=False to keep the skeleton RuntimeError.
"""
from __future__ import annotations

from typing import Any


def _default_engines(repo: Any = None):
    from .forensic import ForensicEngine
    from .gap_tasks import GapTaskCompiler
    from .repo_truth import FakeRepoTruth, LocalRepoTruth, RepoTruthPort

    if repo is None:
        port: RepoTruthPort = FakeRepoTruth(
            {"workflow_default.txt": b"WordflowKernel auto_inject"}
        )
    elif isinstance(repo, RepoTruthPort):
        port = repo
    else:
        port = LocalRepoTruth(repo)
    return ForensicEngine(port), GapTaskCompiler()


class WordflowKernel:
    """Thin orchestrator; engines default-injected unless auto_inject=False."""

    def __init__(
        self,
        audit_engine: Any = None,
        compiler: Any = None,
        trace: Any = None,
        ledger: Any = None,
        checkpoints: Any = None,
        memory: Any = None,
        repo: Any = None,
        auto_inject: bool = True,
    ):
        if auto_inject and (audit_engine is None or compiler is None):
            default_audit, default_compiler = _default_engines(repo)
            if audit_engine is None:
                audit_engine = default_audit
            if compiler is None:
                compiler = default_compiler
        self.audit_engine = audit_engine
        self.compiler = compiler
        self.trace = trace
        self.ledger = ledger
        self.checkpoints = checkpoints
        self.memory = memory
        self.auto_inject = auto_inject

    def audit_to_plan(self, mission_id: str, workspace_id: str, target: str, requirements: list):
        if self.audit_engine is None or self.compiler is None:
            raise RuntimeError("VK-01 skeleton: inject audit_engine+compiler in VK-02/VK-03")
        if self.trace is not None:
            self.trace.emit(mission_id, "AUDIT", "ENTER", {"input": requirements})
        report = self.audit_engine.audit(target, requirements)
        if self.memory is not None:
            self.memory.store(
                {
                    "type": "audit_report",
                    "audit_id": report.audit_id,
                    "status": report.status,
                    "gaps": [g.__dict__ for g in report.gaps],
                },
                workspace_id,
            )
        tasks = self.compiler.compile(report, workspace_id)
        if self.checkpoints is not None:
            self.checkpoints.save(
                mission_id,
                "PLAN",
                {"audit_id": report.audit_id, "task_ids": [t.task_id for t in tasks]},
            )
        if self.ledger is not None:
            self.ledger.append(
                mission_id,
                {
                    "stage": "PLAN",
                    "audit_id": report.audit_id,
                    "tasks": [t.__dict__ for t in tasks],
                },
            )
        return report, tasks
