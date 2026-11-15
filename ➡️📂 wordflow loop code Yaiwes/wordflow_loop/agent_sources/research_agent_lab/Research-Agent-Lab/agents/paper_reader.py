from __future__ import annotations

from dataclasses import asdict

from core.agent_base import Agent, AgentContext, AgentResult
from core.state import ResearchState
from schemas.evidence import Evidence


class PaperReaderAgent(Agent):
    name = "paper_reader"

    def run(self, state: ResearchState, context: AgentContext) -> AgentResult:
        evidence_items: list[Evidence] = []
        parsed_by_paper = {item["paper_id"]: item for item in state.values.get("parsed_papers", [])}
        for paper in state.values.get("selected_papers", []):
            keyword = ", ".join(paper.get("keywords", []))
            paper_id = paper["paper_id"]
            claim = f"{paper.get('title')} is relevant to {state.topic.topic_name}"
            parsed = parsed_by_paper.get(paper_id)
            chunks = parsed.get("chunks", []) if parsed else []
            selected_chunks = _select_evidence_chunks(chunks, paper_id, paper)
            for chunk in selected_chunks:
                evidence_items.append(
                    Evidence(
                        paper_id=paper_id,
                        claim_supported=claim,
                        quote=chunk["text"][:1200],
                        section=chunk.get("section", "Local PDF"),
                        chunk_id=chunk.get("chunk_id", f"{paper_id}:unknown"),
                        support_level="weak",
                    )
                )

        artifact_ids: list[str] = []
        for evidence in evidence_items:
            context.artifact_store.save_json(
                state.run_id, "evidence", evidence.evidence_id, evidence
            )
            artifact_ids.append(evidence.evidence_id)

        state.values["evidence"] = [asdict(item) for item in evidence_items]
        return AgentResult(
            notes=[f"created {len(evidence_items)} evidence records"],
            artifacts={"evidence": artifact_ids},
            values={"evidence_count": len(evidence_items)},
        )


def _select_evidence_chunks(
    chunks: list[dict], paper_id: str, paper: dict
) -> list[dict]:
    patterns = [
        (["abstract"], "Abstract"),
        (["method", "approach", "architecture", "model"], "Method"),
        (["experiment", "result", "evaluation", "ablation"], "Experiments/Results"),
    ]
    selected: list[dict] = []
    found: set[str] = set()
    for keywords, label in patterns:
        for chunk in chunks:
            section = (chunk.get("section") or "").lower()
            if any(kw in section for kw in keywords):
                if label not in found:
                    selected.append(chunk)
                    found.add(label)
                    break
    if not selected:
        if chunks:
            selected.append(chunks[0])
        elif paper.get("abstract"):
            selected.append(
                {"text": paper["abstract"], "section": "Abstract",
                 "chunk_id": f"{paper_id}:abstract"}
            )
    return selected
