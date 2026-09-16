from __future__ import annotations

import argparse
import os
from pathlib import Path

from core.artifact_store import ArtifactStore
from core.run_logger import RunLogger
from memory.sqlite_memory import SQLiteMemoryStore
from schemas.topic_pack import load_topic_pack
from tools.agent_laboratory_adapter import AgentLaboratoryAdapter
from tools.arxiv_tool import ArxivTool
from tools.env_loader import load_env_file, mask_secret
from tools.local_paper_library import LocalPaperLibrary
from tools.model_router import ModelRouter
from tools.tool_registry import build_default_tool_registry
from workflows.factory import build_full_research_workflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="research-agent-lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a research workflow")
    run_parser.add_argument("--topic", required=True, help="Path to a topic pack JSON file")
    run_parser.add_argument("--data-dir", default="data", help="Runtime data directory")
    run_parser.add_argument(
        "--online",
        action="store_true",
        help="Enable online tools such as arXiv when network access is available",
    )
    run_parser.add_argument(
        "--max-papers",
        type=int,
        default=8,
        help="Maximum papers or seed papers to carry through the first pass",
    )
    run_parser.add_argument(
        "--enable-llm",
        action="store_true",
        help="Allow agents with configured model routes to call external LLM APIs",
    )

    agentlab_parser = subparsers.add_parser(
        "agentlab-config",
        help="Generate an Agent Laboratory YAML config from a topic pack",
    )
    agentlab_parser.add_argument("--topic", required=True, help="Path to a topic pack JSON file")
    agentlab_parser.add_argument(
        "--output",
        default="agentlab_configs/generated_agentlab.yaml",
        help="Output YAML path",
    )
    agentlab_parser.add_argument(
        "--agentlab-dir",
        default="external/AgentLaboratory",
        help="Path to the cloned Agent Laboratory repository",
    )
    agentlab_parser.add_argument("--llm-backend", default="gpt-4o")

    check_parser = subparsers.add_parser(
        "check-config",
        help="Check topic config, local papers, and model-route availability without exposing secrets",
    )
    check_parser.add_argument("--topic", required=True, help="Path to a topic pack JSON file")

    return parser


def run_workflow(args: argparse.Namespace) -> int:
    load_env_file(".env")
    topic = load_topic_pack(Path(args.topic))
    data_dir = Path(args.data_dir)
    store = ArtifactStore(data_dir / "runs")
    memory = SQLiteMemoryStore(data_dir / "memory.sqlite3")
    logger = RunLogger()
    tools = build_default_tool_registry()

    if args.online:
        tools.register(ArxivTool(max_results=args.max_papers))

    workflow = build_full_research_workflow(
        artifact_store=store,
        memory_store=memory,
        tool_registry=tools,
        logger=logger,
        max_papers=args.max_papers,
        enable_llm=args.enable_llm,
    )
    state = workflow.run(topic)

    print(f"run_id={state.run_id}")
    print(f"stage={state.stage}")
    print(f"run_dir={store.run_dir(state.run_id)}")
    print(f"review_status={state.values.get('review_status', 'unknown')}")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "run":
        return run_workflow(args)
    if args.command == "agentlab-config":
        load_env_file(".env")
        topic = load_topic_pack(Path(args.topic))
        adapter = AgentLaboratoryAdapter(args.agentlab_dir)
        config = adapter.write_config(topic, args.output, llm_backend=args.llm_backend)
        print(f"config={config.path}")
        print("command=" + " ".join(config.command))
        return 0
    if args.command == "check-config":
        loaded = load_env_file(".env")
        topic = load_topic_pack(Path(args.topic))
        papers = LocalPaperLibrary().scan(topic)
        router = ModelRouter(topic)
        print(f"topic={topic.topic_name}")
        print(f"env_file_loaded_keys={','.join(sorted(loaded.keys())) if loaded else '<none>'}")
        deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
        print(f"DEEPSEEK_API_KEY_present={bool(deepseek_key)}")
        print(f"DEEPSEEK_API_KEY_mask={mask_secret(deepseek_key)}")
        print(f"local_paper_count={len(papers)}")
        for agent_name in [
            "paper_triage",
            "synthesis",
            "method_card_extractor",
            "experiment_planner",
            "reviewer_agent",
            "result_parser",
        ]:
            route = router.route_for(agent_name)
            print(
                f"route[{agent_name}] provider={route.provider} model={route.model} "
                f"difficulty={route.task_difficulty or '<unset>'} "
                f"enabled={route.enabled} api_key_env={route.api_key_env}"
            )
        return 0
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
