from __future__ import annotations

from agents import (
    CodebaseAnalyzerAgent,
    DeveloperAgent,
    EvidenceCheckerAgent,
    ExperimentPlannerAgent,
    LiteratureSearchAgent,
    LocalPaperLibraryAgent,
    LocalPaperParserAgent,
    MethodCardExtractorAgent,
    OpportunityAgent,
    PaperReaderAgent,
    PaperTriageAgent,
    ResearchManagerAgent,
    ReviewerAgent,
    SynthesisAgent,
)
from core.artifact_store import ArtifactStore
from core.run_logger import RunLogger
from core.workflow import Workflow
from tools.tool_registry import ToolRegistry


def build_full_research_workflow(
    artifact_store: ArtifactStore,
    memory_store: object,
    tool_registry: ToolRegistry,
    logger: RunLogger,
    max_papers: int = 8,
    enable_llm: bool = False,
) -> Workflow:
    return Workflow(
        name="full_research_loop_v1",
        agents=[
            ResearchManagerAgent(),
            LocalPaperLibraryAgent(),
            LiteratureSearchAgent(),
            PaperTriageAgent(),
            LocalPaperParserAgent(),
            PaperReaderAgent(),
            EvidenceCheckerAgent(),
            MethodCardExtractorAgent(),
            SynthesisAgent(),
            CodebaseAnalyzerAgent(),
            OpportunityAgent(),
            ExperimentPlannerAgent(),
            DeveloperAgent(),
            ReviewerAgent(),
        ],
        artifact_store=artifact_store,
        memory_store=memory_store,
        tool_registry=tool_registry,
        logger=logger,
        settings={"max_papers": max_papers, "enable_llm": enable_llm},
    )
