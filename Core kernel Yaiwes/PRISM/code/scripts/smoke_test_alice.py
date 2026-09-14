from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mmem.config import EmbeddingConfig, MMemConfig
from mmem.ingestion.pipeline import IngestionPipeline
from mmem.retrieval.search import bundle_search
from mmem.utils.embedding import EmbeddingModel

CHUNKS = [
    "Alice joined Acme Corp as a software engineer in January 2020.",
    "Alice got promoted to senior engineer at Acme Corp in March 2021.",
    "Alice and Bob started an ML project in June 2022; Bob handles the data pipeline.",
    "Alice left Acme Corp in September 2023; promotion pressure was the main reason.",
    "Alice and Bob co-founded NeuralEdge in February 2024.",
]

QUERIES = [
    "What is Alice's job?",
    "What happened before Alice left Acme?",
    "What does Bob do?",
    "Tell me about Acme Corp",
    "Who co-founded NeuralEdge?",
]

class RuleBasedLLM:
    """Returns deterministic extraction JSON keyed by known chunks."""

    def __init__(self) -> None:
        self._payloads = {
            CHUNKS[0]: {
                "episode_summary": "Alice joined Acme Corp as a software engineer in January 2020.",
                "entities": [
                    {"name": "Alice", "entity_type": "person"},
                    {"name": "Acme Corp", "entity_type": "organization"},
                    {"name": "software engineer", "entity_type": "concept"},
                ],
                "facet_points": [
                    {"content": "Alice joined Acme Corp in January 2020.", "related_entity_name": "Alice", "timestamp_text": "2020"},
                    {"content": "Alice worked as a software engineer.", "related_entity_name": "Alice", "timestamp_text": "2020"},
                ],
                "facets": [{"theme": "Alice career at Acme", "facet_point_indices": [0, 1]}],
                "temporal_info": [{"subject": "Alice", "time_expression": "January 2020", "normalized_time": "2020", "relation": "at"}],
            },
            CHUNKS[1]: {
                "episode_summary": "Alice was promoted to senior engineer at Acme Corp in March 2021.",
                "entities": [
                    {"name": "Alice", "entity_type": "person"},
                    {"name": "Acme Corp", "entity_type": "organization"},
                    {"name": "senior engineer", "entity_type": "concept"},
                ],
                "facet_points": [
                    {"content": "Alice got promoted at Acme Corp.", "related_entity_name": "Alice", "timestamp_text": "2021"},
                    {"content": "Alice became a senior engineer.", "related_entity_name": "Alice", "timestamp_text": "2021"},
                ],
                "facets": [{"theme": "Alice promotion and role", "facet_point_indices": [0, 1]}],
                "temporal_info": [{"subject": "Alice", "time_expression": "March 2021", "normalized_time": "2021", "relation": "at"}],
            },
            CHUNKS[2]: {
                "episode_summary": "Alice and Bob started an ML project in June 2022 and Bob handled the data pipeline.",
                "entities": [
                    {"name": "Alice", "entity_type": "person"},
                    {"name": "Bob", "entity_type": "person"},
                    {"name": "ML project", "entity_type": "concept"},
                    {"name": "data pipeline", "entity_type": "concept"},
                ],
                "facet_points": [
                    {"content": "Alice and Bob started an ML project.", "related_entity_name": "Alice", "timestamp_text": "2022"},
                    {"content": "Bob handled the data pipeline.", "related_entity_name": "Bob", "timestamp_text": "2022"},
                ],
                "facets": [{"theme": "Alice and Bob project work", "facet_point_indices": [0, 1]}],
                "temporal_info": [{"subject": "Alice and Bob", "time_expression": "June 2022", "normalized_time": "2022", "relation": "at"}],
            },
            CHUNKS[3]: {
                "episode_summary": "Alice left Acme Corp in September 2023 due to promotion pressure.",
                "entities": [
                    {"name": "Alice", "entity_type": "person"},
                    {"name": "Acme Corp", "entity_type": "organization"},
                    {"name": "promotion pressure", "entity_type": "concept"},
                ],
                "facet_points": [
                    {"content": "Alice left Acme Corp.", "related_entity_name": "Alice", "timestamp_text": "2023"},
                    {"content": "Promotion pressure was the main reason for leaving.", "related_entity_name": "Alice", "timestamp_text": "2023"},
                ],
                "facets": [{"theme": "Alice departure from Acme", "facet_point_indices": [0, 1]}],
                "temporal_info": [{"subject": "Alice", "time_expression": "September 2023", "normalized_time": "2023", "relation": "at"}],
            },
            CHUNKS[4]: {
                "episode_summary": "Alice and Bob co-founded NeuralEdge in February 2024.",
                "entities": [
                    {"name": "Alice", "entity_type": "person"},
                    {"name": "Bob", "entity_type": "person"},
                    {"name": "NeuralEdge", "entity_type": "organization"},
                ],
                "facet_points": [
                    {"content": "Alice and Bob co-founded NeuralEdge.", "related_entity_name": "Alice", "timestamp_text": "2024"},
                    {"content": "Bob co-founded NeuralEdge with Alice.", "related_entity_name": "Bob", "timestamp_text": "2024"},
                ],
                "facets": [{"theme": "NeuralEdge founding", "facet_point_indices": [0, 1]}],
                "temporal_info": [{"subject": "Alice and Bob", "time_expression": "February 2024", "normalized_time": "2024", "relation": "at"}],
            },
        }

    def chat_json(
        self,
        prompt: str,
        model: str | None = None,
        system: str = "",
        temperature: float | None = None,
    ) -> dict[str, Any]:
        if "causal reasoning engine" in prompt.lower():
            return {"causal_pairs": []}

        for chunk, payload in self._payloads.items():
            if chunk in prompt:
                return payload

        return {"episode_summary": "fallback summary", "entities": []}


def _print_stats(title: str, stats: dict[str, Any]) -> None:
    print(f"\n=== {title} ===")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


def main() -> None:
    cfg = MMemConfig()
    cfg.write.enable_causal_consolidation = False

    # Use real sentence-transformers embedder for this smoke test run.
    embedder = EmbeddingModel(
        config=EmbeddingConfig(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            dimension=384,
            device="cpu",
        )
    )
    llm = RuleBasedLLM()

    pipeline = IngestionPipeline(config=cfg, embedder=embedder, llm_client=llm)

    for i, chunk in enumerate(CHUNKS, 1):
        pipeline.ingest(chunk)
        _print_stats(f"After ingest {i}", pipeline.stats())

    ckpt_dir = Path("tmp/smoke_ckpt")
    if ckpt_dir.exists():
        shutil.rmtree(ckpt_dir)
    pipeline.save_checkpoint(ckpt_dir)
    print(f"\nCheckpoint saved to: {ckpt_dir}")

    # API is classmethod; this is the canonical restore path.
    pipeline = IngestionPipeline.load_checkpoint(
        ckpt_dir,
        config=cfg,
        embedder=embedder,
        llm_client=llm,
    )
    _print_stats("After reload", pipeline.stats())

    for q in QUERIES:
        print(f"\n\n=== Query: {q} ===")
        result = bundle_search(
            q,
            pipeline.graph,
            pipeline.vector_store,
            embedder,
            config=cfg,
            top_k=3,
            display_mode="detail",
        )
        print(f"bundles={len(result.bundles)}")
        for rank, bundle in enumerate(result.bundles[:3], 1):
            print(
                f"  [{rank}] episode_id={bundle.episode_id} "
                f"score={bundle.score:.6f} "
                f"best_path={bundle.best_path} "
                f"best_path_detail={bundle.best_path_detail}"
            )

        if "before Alice left" in q:
            print(f"\n  debug_info={json.dumps(result.debug_info, indent=2, ensure_ascii=False)}")
            for bundle in result.bundles[:3]:
                print(f"\n  Episode {bundle.episode_id} all paths:")
                for pc in bundle.all_paths:
                    print(f"    {pc.path_type}: cost={pc.cost:.6f}")

        preview = result.context_text[:800]
        print("context_text_preview:")
        print(preview if preview else "<empty>")


if __name__ == "__main__":
    main()
