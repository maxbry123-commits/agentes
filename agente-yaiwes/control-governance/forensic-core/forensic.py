from __future__ import annotations

import ast
import re

from .models import AuditReport, Evidence, Gap, uid
from .repo_truth import RepoTruthPort


class ForensicEngine:
    """Claim vs evidence auditor. Deterministic markers; no LLM."""

    def __init__(self, repo: RepoTruthPort):
        self.repo = repo

    def _symbols(self, text: str, suffix: str) -> set[str]:
        if suffix != ".py":
            return set(re.findall(r"\b(?:class|def)\s+([A-Za-z_]\w*)", text))
        try:
            tree = ast.parse(text)
            return {
                n.name
                for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            }
        except SyntaxError:
            return set()

    def audit(self, target, requirements=None, revision=None):
        files = self.repo.list_files(revision)
        evidence = [
            Evidence(uid("ev"), "repo_file", f.path, f.sha, {"size": f.size}) for f in files
        ]
        requirements = requirements or []
        gaps = []
        matches = partial = missing = contradictions = 0

        all_text: dict[str, str] = {}
        for f in files:
            try:
                all_text[f.path] = self.repo.read_file(f.path, revision).decode("utf-8", "ignore")
            except Exception:
                all_text[f.path] = ""

        joined = "\n".join(all_text.values())
        for req in requirements:
            if isinstance(req, str):
                req = {"requirement": req, "marker": req}
            marker = req.get("marker", req.get("requirement", ""))
            target_path = req.get("path")
            if target_path and target_path in all_text:
                text = all_text[target_path]
                if marker and marker in text:
                    matches += 1
                    continue
                partial += 1
                gaps.append(
                    Gap(
                        uid("gap"),
                        req.get("requirement", marker),
                        "PARTIAL",
                        req.get("severity", "MEDIUM"),
                        recommendation=req.get("recommendation", ""),
                    )
                )
            elif marker and marker in joined:
                matches += 1
            else:
                missing += 1
                gaps.append(
                    Gap(
                        uid("gap"),
                        req.get("requirement", marker),
                        "MISSING",
                        req.get("severity", "HIGH"),
                        recommendation=req.get("recommendation", ""),
                    )
                )

        status = "PASS" if not gaps else "GAPS_FOUND"
        return AuditReport(
            uid("audit"),
            target,
            revision or self.repo.head(revision),
            status,
            len(requirements),
            matches,
            partial,
            missing,
            contradictions,
            gaps,
            evidence,
        )
