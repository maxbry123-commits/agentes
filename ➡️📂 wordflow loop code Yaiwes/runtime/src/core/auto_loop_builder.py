"""Run-scoped Crazy Wall / STATE / CHECKPOINT / DSL-DAG builder.

This additive builder never edits the global 30/30 CODE_GRAPH truth anchors.
It creates a new isolated run plan from a verified ProjectIntakeResult.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping

_RUN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


class AutoLoopError(ValueError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _as_mapping(intake: Any) -> Mapping[str, Any]:
    if hasattr(intake, "__dataclass_fields__"):
        value=asdict(intake)
    elif isinstance(intake, Mapping):
        value=dict(intake)
    else:
        raise AutoLoopError("PROJECT_INTAKE_MAPPING_REQUIRED")
    if value.get("schema") != "yaiwes.project-intake/v1":
        raise AutoLoopError("PROJECT_INTAKE_SCHEMA_REQUIRED")
    return value


def build_loop_documents(*, intake: Any, instruction: str, run_id: str) -> dict[str, str]:
    data=_as_mapping(intake)
    instruction=instruction.strip()
    run_id=run_id.strip()
    if not instruction:
        raise AutoLoopError("INSTRUCTION_REQUIRED")
    if not _RUN.fullmatch(run_id):
        raise AutoLoopError("RUN_ID_INVALID")

    project_id=str(data.get("project_id","")).strip()
    profile=str(data.get("profile","")).strip()
    destination=str(data.get("destination","")).strip()
    if not project_id or profile not in {"backend","frontend","general"} or not destination:
        raise AutoLoopError("PROJECT_INTAKE_INCOMPLETE")

    reqs=data.get("requirements", [])
    if not isinstance(reqs, (list, tuple)):
        raise AutoLoopError("REQUIREMENTS_LIST_REQUIRED")

    base_nodes=[
        {"id":"RUN-001","task":"Read literal input + verified intake","depends_on":[],"state":"PENDING","write_scope":None},
        {"id":"RUN-002","task":"Build/review architecture context","depends_on":["RUN-001"],"state":"PENDING","write_scope":None},
        {"id":"RUN-003","task":"Select 3-5 relevant verified skills","depends_on":["RUN-002"],"state":"PENDING","write_scope":None},
    ]
    req_nodes=[]
    for idx, req in enumerate(reqs, 1):
        req_id=f"REQ-{idx:03d}"
        statement=str(req.get("statement") or req.get("requirement") or req.get("id") or f"requirement {idx}").strip()
        source_id=str(req.get("source_id","")).strip()
        req_nodes.append({
            "id":req_id,
            "task":statement,
            "source_id":source_id,
            "depends_on":["RUN-003"],
            "state":"PENDING",
            "write_scope":destination,
            "acceptance":["implementation_or_verified_no_change","tests_or_runtime_evidence"],
            "evidence":[],
        })
    implementation_deps=[n["id"] for n in req_nodes] or ["RUN-003"]
    tail=[
        {"id":"RUN-900","task":"Sheriff + execution/reuse/adapt/generate gate","depends_on":implementation_deps,"state":"PENDING","write_scope":destination},
        {"id":"RUN-910","task":"Backend/frontend completion gate","depends_on":["RUN-900"],"state":"PENDING","write_scope":None},
        {"id":"RUN-920","task":"Persist evidence + completion audit","depends_on":["RUN-910"],"state":"PENDING","write_scope":None},
    ]
    nodes=base_nodes+req_nodes+tail
    edges=[{"from":dep,"to":node["id"]} for node in nodes for dep in node.get("depends_on",[])]

    task_contract={
        "schema":"yaiwes.task-contract/v1",
        "run_id":run_id,
        "project_id":project_id,
        "profile":profile,
        "goal":instruction,
        "destination":destination,
        "input_file_count":int(data.get("file_count",0)),
        "acceptance_policy":"EVIDENCE_REQUIRED",
        "frontend_policy":"CODE+BUILD+RUNTIME+BROWSER+INTERACTION+DOM_OR_VISUAL+MOBILE_TOUCH" if profile=="frontend" else None,
        "execution_authorized":False,
    }
    dag={
        "schema":"yaiwes.run-dag/v1",
        "run_id":run_id,
        "dsl":"INPUT_LITERAL -> AUDIT -> ARCHITECTURE -> SKILLS_3_5 -> SHERIFF -> EXECUTE -> COMPLETION_GATE -> EVIDENCE",
        "nodes":nodes,
        "edges":edges,
    }
    crazy={
        "schema":"yaiwes.crazy-wall.run/v1",
        "run_id":run_id,
        "project_id":project_id,
        "mode":"FAIL_CLOSED_EXECUTION_LOOP",
        "queue_policy":"DAG_DEPENDENCIES_PLUS_PARALLEL_INDEPENDENT",
        "nodes":nodes,
        "current_node":None,
        "status":"READY",
    }
    state={
        "schema":"yaiwes.run-state/v1",
        "run_id":run_id,
        "project_id":project_id,
        "profile":profile,
        "status":"READY",
        "current_node":None,
        "closed_nodes":[],
        "blocked_nodes":[],
        "global_code_graph_30_of_30_untouched":True,
        "task_contract_sha256":_sha(task_contract),
        "dag_sha256":_sha(dag),
    }
    checkpoint={
        "schema":"yaiwes.run-checkpoint/v1",
        "run_id":run_id,
        "status":"READY",
        "state_sha256":_sha(state),
        "crazy_wall_sha256":_sha(crazy),
        "next_action":"CLAIM_FIRST_READY_NODE",
    }
    bitacora=(
        f"# YAIWES RUN {run_id}\n\n"
        f"- project_id: `{project_id}`\n"
        f"- profile: `{profile}`\n"
        f"- status: `READY`\n"
        f"- destination: `{destination}`\n"
        f"- input files: `{data.get('file_count',0)}`\n"
        f"- global CODE_GRAPH 30/30 modified: `NO`\n\n"
        "## Goal\n\n"+instruction+"\n\n"
        "## Loop\n\nREAD → CLAIM → SKILLS → STRUCTURED ACTION → SHERIFF → EXECUTE → OBSERVE → TEST → ACCEPTANCE → EVIDENCE → NEXT\n"
    )
    files={
        "TASK-CONTRACT.json":json.dumps(task_contract,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
        "DAG.json":json.dumps(dag,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
        "CRAZY-WALL.json":json.dumps(crazy,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
        "STATE.json":json.dumps(state,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
        "CHECKPOINT.json":json.dumps(checkpoint,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
        "BITACORA.md":bitacora,
        "ARCHITECTURE.json":json.dumps(data.get("architecture",{}),ensure_ascii=False,indent=2,sort_keys=True)+"\n",
        "SOURCE.json":json.dumps({"files":data.get("files",[]),"risks":data.get("risks",[])},ensure_ascii=False,indent=2,sort_keys=True)+"\n",
    }
    return files


def persist_run_documents(
    *, authorized_root: Path, run_id: str, documents: Mapping[str, str], mutation_authorized: bool
) -> Path:
    if not mutation_authorized:
        raise PermissionError("MUTATION_NOT_AUTHORIZED")
    if not _RUN.fullmatch(run_id):
        raise AutoLoopError("RUN_ID_INVALID")
    root=authorized_root.resolve()
    target=(root/"workspace"/"runs"/run_id).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise AutoLoopError("RUN_DESTINATION_OUTSIDE_ROOT") from exc
    if target.exists() and any(target.iterdir()):
        raise AutoLoopError("RUN_ID_ALREADY_EXISTS")
    allowed={"TASK-CONTRACT.json","DAG.json","CRAZY-WALL.json","STATE.json","CHECKPOINT.json","BITACORA.md","ARCHITECTURE.json","SOURCE.json"}
    if set(documents) != allowed:
        raise AutoLoopError("RUN_DOCUMENT_SET_INVALID")
    target.mkdir(parents=True,exist_ok=True)
    for name,content in documents.items():
        tmp=target/(name+".tmp")
        final=target/name
        tmp.write_text(content,encoding="utf-8")
        os.replace(tmp,final)
        if final.read_text(encoding="utf-8") != content:
            raise AutoLoopError("RUN_DOCUMENT_READBACK_MISMATCH:"+name)
    return target
