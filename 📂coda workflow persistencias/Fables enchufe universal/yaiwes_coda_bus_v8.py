from __future__ import annotations

import concurrent.futures
import threading
from pathlib import Path
from typing import Any, Iterable

import yaiwes_coda_bus_v7 as v7
from yaiwes_coda_persistence_v8 import PersistenceBackend, SQLiteDurableStore

core = v7.core
SCHEMA = "yaiwes.coda.bus/v8"


def run_coda_chain(
    state_root: str | Path,
    task_id: str,
    task: dict[str, Any] | None = None,
    *,
    broker: v7.ToolBroker | None = None,
    knowledge_root: str | Path | None = None,
    durable: PersistenceBackend | None = None,
) -> dict[str, Any]:
    """Run or resume the 24-link CODA chain.

    V8 keeps V7 research/tool discovery and the V6.3 real internal workflows,
    but adds a transactional durable control plane. A restart resumes from the
    first component without a committed checkpoint instead of replaying links
    already completed.
    """
    state_root = Path(state_root)
    task = dict(task or {})
    durable = durable or SQLiteDurableStore(state_root / "CODA-DURABLE.sqlite")
    workflow_id = v7._safe_id(task_id)

    durable.begin_workflow(workflow_id, task)
    cached = durable.cached_report(workflow_id)
    if cached is not None:
        return cached

    broker = broker or v7.ToolBroker(v7.McpRegistryDiscovery())
    research_stage = v7.CodaResearchStage(broker)
    knowledge = v7.KnowledgeStore(knowledge_root or (state_root / "CODA-KNOWLEDGE"))
    components = core._component_roots_strict()

    completed = durable.load_completed(workflow_id)
    internal_history = [x["internal_state"] for x in completed]
    bus_history = [x["evidence"] for x in completed]

    if completed:
        current_output: Any = completed[-1]["output"]
        start_ordinal = completed[-1]["component"] + 1
    else:
        current_output = {
            "schema": SCHEMA,
            "task_id": task_id,
            "task": task,
            "origin": "CODA_INPUT",
        }
        start_ordinal = 1

    for ordinal in range(start_ordinal, 25):
        label = f"YAIWES {ordinal:02d}"
        try:
            durable.append_event(
                workflow_id,
                ordinal,
                "RESEARCH_STARTED",
                {"component": label, "previous_output_hash": v7._digest(current_output)},
            )
            learned = knowledge.recent(label)
            research = research_stage.run(label, task, current_output, learned)
            durable.append_event(
                workflow_id,
                ordinal,
                "RESEARCH_COMPLETED",
                {
                    "component": label,
                    "research_digest": v7._digest(research),
                    "tool_candidates": len(research.get("tool_candidates", [])),
                    "status": research.get("research_status"),
                },
            )

            enriched_input = {
                "schema": SCHEMA,
                "task_id": task_id,
                "component": label,
                "previous_output": v7._jsonable(current_output),
                "previous_output_hash": v7._digest(current_output),
                "research": research,
                "learned_context": v7._jsonable(learned),
            }

            durable.append_event(
                workflow_id,
                ordinal,
                "INTERNAL_WORKFLOW_STARTED",
                {"component": label, "input_hash": v7._digest(enriched_input)},
            )
            internal_state, next_output = core._run_link(
                ordinal,
                components[ordinal],
                task_id,
                task,
                enriched_input,
                state_root,
                internal_history,
            )
            if internal_state.get("input_hash") != v7._digest(enriched_input):
                raise RuntimeError(f"{label} did not receive its research-enriched CODA input")
            if ordinal > 1 and enriched_input["previous_output_hash"] != internal_history[-1]["output_hash"]:
                raise RuntimeError(f"handoff continuity failure before {label}")

            learned_record = {
                "schema": SCHEMA,
                "task_id": task_id,
                "component": label,
                "research": research,
                "workflow": {
                    "status": internal_state.get("workflow_status"),
                    "source": internal_state.get("workflow_source"),
                    "symbol": internal_state.get("workflow_symbol"),
                    "engine": internal_state.get("engine"),
                    "output_hash": internal_state.get("output_hash"),
                },
                "lesson": {
                    "input_hash": internal_state.get("input_hash"),
                    "output_hash": internal_state.get("output_hash"),
                    "research_digest": v7._digest(research),
                    "tool_candidates": len(research.get("tool_candidates", [])),
                },
            }
            knowledge_path = knowledge.save(label, task_id, learned_record)

            evidence = {
                "order": ordinal,
                "component": label,
                "research_status": research["research_status"],
                "research_digest": v7._digest(research),
                "tool_candidates": len(research.get("tool_candidates", [])),
                "knowledge_path": knowledge_path,
                "internal_state": internal_state,
                "durable_backend": "sqlite-wal",
            }
            durable.checkpoint(
                workflow_id,
                ordinal,
                label,
                evidence,
                internal_state,
                next_output,
                research,
            )
            bus_history.append(evidence)
            internal_history.append(internal_state)
            current_output = next_output
        except Exception as exc:
            durable.mark_interrupted(workflow_id, ordinal, exc)
            raise

    if len(bus_history) != 24:
        raise RuntimeError(f"CODA chain blocked: durable checkpoints={len(bus_history)}/24")
    if any(x["internal_state"].get("workflow_status") != "COMPLETED" for x in bus_history):
        raise RuntimeError("CODA chain blocked: all 24 internal workflows must complete")

    plug = v7._plug_state(task_id, current_output, bus_history)
    if not plug["continuity_ok"]:
        raise RuntimeError("universal plug continuity failure")
    core._atomic_write(
        state_root / "UNIVERSAL_PLUG" / f"{v7._safe_id(task_id)}.json",
        plug,
    )

    report = {
        "schema": SCHEMA,
        "task_id": task_id,
        "components": 24,
        "research_cycles": 24,
        "real_internal_workflows_executed": 24,
        "completed_internal_workflows": 24,
        "universal_plug_after_component_24": True,
        "durable_backend": "sqlite-wal",
        "recovered_components": start_ordinal - 1,
        "resume_from_component": start_ordinal,
        "status": "CLOSED_24_CODA_DURABLE",
        "final_output": v7._jsonable(current_output),
        "evidence": bus_history,
    }
    core._atomic_write(
        state_root / "REPORTS" / f"{v7._safe_id(task_id)}.json",
        report,
    )
    durable.complete_workflow(workflow_id, report)
    return report


def run_parallel_tasks(
    state_root: str | Path,
    tasks: Iterable[dict[str, Any]],
    *,
    broker: v7.ToolBroker | None = None,
    max_workers: int = 4,
    durable: SQLiteDurableStore | None = None,
) -> dict[str, Any]:
    """Durably enqueue independent tasks and fan them out across workers."""
    state_root = Path(state_root)
    durable = durable or SQLiteDurableStore(state_root / "CODA-DURABLE.sqlite")
    broker = broker or v7.ToolBroker(v7.McpRegistryDiscovery())
    knowledge_root = state_root / "CODA-KNOWLEDGE"

    prepared: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(tasks, 1):
        data = dict(item)
        task_id = str(data.pop("task_id", f"branch-{index}"))
        if task_id in seen:
            raise ValueError(f"duplicate task_id: {task_id}")
        seen.add(task_id)
        priority = int(data.pop("priority", 5))
        durable.enqueue(task_id, data, priority)
        prepared.append(task_id)

    if not prepared:
        return {"schema": SCHEMA, "branches": 0, "status": "NO_TASKS", "results": []}

    results: list[dict[str, Any]] = []
    results_lock = threading.Lock()

    def worker(worker_no: int) -> None:
        worker_id = f"yaiwes-coda-v8-{worker_no}"
        while True:
            claimed = durable.claim(worker_id, allowed_task_ids=prepared)
            if claimed is None:
                return
            claimed_task_id = str(claimed["task_id"])
            branch_root = state_root / "BRANCHES" / v7._safe_id(claimed_task_id)
            try:
                report = run_coda_chain(
                    branch_root,
                    claimed_task_id,
                    claimed["payload"],
                    broker=broker,
                    knowledge_root=knowledge_root,
                    durable=durable,
                )
                durable.finish_queue(claimed_task_id, True)
                result = {"task_id": claimed_task_id, "status": "COMPLETED", "report": report}
            except Exception as exc:
                durable.finish_queue(claimed_task_id, False, str(exc)[:2000])
                result = {"task_id": claimed_task_id, "status": "FAILED", "error": str(exc)}
            with results_lock:
                results.append(result)

    workers = max(1, min(max_workers, len(prepared)))
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=workers,
        thread_name_prefix="yaiwes-coda-v8",
    ) as pool:
        futures = [pool.submit(worker, i + 1) for i in range(workers)]
        for future in futures:
            future.result()

    observed = {x["task_id"] for x in results}
    for task_id in prepared:
        if task_id in observed:
            continue
        row = durable.queue_state(task_id)
        cached = durable.cached_report(v7._safe_id(task_id))
        if row and row["status"] == "DONE" and cached is not None:
            results.append({"task_id": task_id, "status": "COMPLETED", "report": cached})

    results.sort(key=lambda x: x["task_id"])
    status = (
        "COMPLETED"
        if len(results) == len(prepared) and all(x["status"] == "COMPLETED" for x in results)
        else "PARTIAL_FAILURE"
    )
    report = {
        "schema": SCHEMA,
        "branches": len(results),
        "status": status,
        "durable_queue": True,
        "results": results,
    }
    core._atomic_write(state_root / "PARALLEL-REPORT-V8.json", report)
    return report
