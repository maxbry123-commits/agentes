"""Kernel LINK to Wordflow reception convert + locate + ingest.

Inbox files: extensions/wordflow/reception/
This module does not duplicate convert logic.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_MAX_CONTEXT = 20_000_000

_RECEPTION_DIR = "extensions/wordflow/reception"
_KERNEL_RECEPTION = "extensions/wordflow_kernel/reception"
_KERNEL_ROOT = Path(__file__).resolve().parents[1]

_PHASE_PATHS = {
    "inbox": f"{_RECEPTION_DIR}/",
    "kernel": "extensions/wordflow_kernel/",
    "engine": "extensions/wordflow/engine/",
    "standards": "extensions/wordflow/standards/",
    "loop": "extensions/maxbry_loop/",
    "deploy": "extensions/github_deploy/",
    "pipeline": "PIPELINE/",
    "plugin": "extensions/wordflow_kernel/ficha.v2.json",
}


def _impl():
    try:
        from extensions.wordflow.reception import convert as impl

        return impl
    except ImportError:
        try:
            from wordflow.reception import convert as impl  # type: ignore

            return impl
        except ImportError:
            return None


def convert(
    input_block: dict[str, Any] | None,
    *,
    use_sdpa: bool = False,
    branch: str = "default",
    max_context: int = DEFAULT_MAX_CONTEXT,
) -> dict[str, Any]:
    impl = _impl()
    if impl is None:
        return {
            "ok": False,
            "error": "RECEPTION_IMPL_MISSING",
            "expected": f"{_RECEPTION_DIR}/convert.py",
            "kernel_link": _KERNEL_RECEPTION,
        }
    return impl.convert(
        input_block,
        use_sdpa=use_sdpa,
        branch=branch,
        max_context=max_context,
    )


def run_mcr(input_block: dict[str, Any] | None) -> dict[str, Any]:
    impl = _impl()
    if impl is None:
        return {"ok": False, "error": "RECEPTION_IMPL_MISSING"}
    return impl.run_mcr(input_block)


def locate(kind: str = "inbox") -> dict[str, Any]:
    kind = (kind or "inbox").strip().lower()
    paths = {
        "inbox": f"{_RECEPTION_DIR}/RECEPTION_agentes.md",
        "template": f"{_RECEPTION_DIR}/RECEPTION_TEMPLATE.md",
        "links": f"{_RECEPTION_DIR}/KNOWLEDGE_RECEPTION_LINKS.md",
        "guide": f"{_RECEPTION_DIR}/advanced_engineering_code_standard_guia_maestra.md",
        "convert": f"{_RECEPTION_DIR}/convert.py",
        "kernel": _KERNEL_RECEPTION,
        "motor": "extensions/wordflow/motors/kernel_ext/motor.py",
        **{f"phase_{k}": v for k, v in _PHASE_PATHS.items()},
    }
    return {
        "ok": True,
        "kind": kind,
        "path": paths.get(kind, paths.get(f"phase_{kind}", paths["inbox"])),
        "catalog": paths,
        "url_inbox": "https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow/reception",
        "url_kernel": "https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow_kernel/reception",
    }


def _as_block(input_block: dict[str, Any] | None, converted: dict[str, Any]) -> dict[str, Any]:
    text = ""
    if isinstance(converted, dict):
        text = str((converted.get("normalized") or {}).get("text") or "")
    if isinstance(input_block, dict):
        block = dict(input_block)
        if text:
            block["raw_text"] = text
            block.setdefault("text", text)
        block.setdefault("schema_version", "1.0")
        block.setdefault("source_type", str(block.get("source") or "reception"))
        block.setdefault("block_id", "blk_reception")
        block.setdefault("quality_bar", "never_MVP")
        block.setdefault("goals_hint", [])
        return block
    return {
        "schema_version": "1.0",
        "block_id": "blk_reception",
        "source_type": "reception",
        "raw_text": text,
        "quality_bar": "never_MVP",
        "goals_hint": [],
    }


def _compile(input_block: dict[str, Any] | None, converted: dict[str, Any]) -> dict[str, Any]:
    try:
        from extensions.wordflow.engine.input_compiler import compile_or_reason
    except ImportError:
        try:
            from wordflow.engine.input_compiler import compile_or_reason
        except ImportError:
            return {"ok": False, "error": "INPUT_COMPILER_MISSING", "invoked": False}
    try:
        ok, payload = compile_or_reason(_as_block(input_block, converted))
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "invoked": True}
    if ok:
        return {"ok": True, "invoked": True, "contract": payload}
    return {"ok": False, "invoked": True, "error": payload}


def _classify(text: str) -> dict[str, Any]:
    try:
        from extensions.wordflow.engine.task_classifier import classify_task, decision_gate
    except ImportError:
        try:
            from wordflow.engine.task_classifier import classify_task, decision_gate
        except ImportError:
            return {"ok": False, "error": "TASK_CLASSIFIER_MISSING", "invoked": False}
    classification = classify_task(text or "")
    return {
        "ok": True,
        "invoked": True,
        "classification": classification,
        "gate": decision_gate(classification),
    }


def locate_phase(text: str = "") -> dict[str, Any]:
    """Map text → exact repo path. Does not write files unless dest is supplied."""
    low = (text or "").lower()
    phase = "engine"
    if any(k in low for k in ("wordflow_kernel", "extensión kernel", "extension kernel")):
        phase = "kernel"
    elif "reception" in low:
        phase = "inbox"
    elif any(k in low for k in ("forensic_core", "standards", "copy-first", "c-19")):
        phase = "standards"
    elif any(k in low for k in ("maxbry_loop", "stage_hooks")):
        phase = "loop"
    elif any(k in low for k in ("github_deploy", "plan_push", "token_ref", "apply_push")):
        phase = "deploy"
    elif any(k in low for k in ("arquitectura", "pipeline/", "handoff")):
        phase = "pipeline"
    return {
        "ok": True,
        "phase": phase,
        "path": _PHASE_PATHS[phase],
        "wrote": False,
        "apply": "external",
        "contract": "LOCATE_ONLY",
    }


def apply_phase_plan(phase: dict[str, Any], dest: str | Path) -> dict[str, Any]:
    """Write phase plan JSON. Not git apply. Contract: plan artifact only."""
    path = Path(dest)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "contract": "LOCATE_ONLY",
        "git_apply": False,
        "phase": phase.get("phase"),
        "path": phase.get("path"),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "wrote": True,
        "path": str(path),
        "git_apply": False,
        "contract": "LOCATE_ONLY",
    }


def _resolve_ficha(module_root: str) -> Path:
    packaged = _KERNEL_ROOT / "ficha.v2.json"
    if packaged.is_file():
        return packaged
    return Path(module_root) / "ficha.v2.json"


def attach_plugin(module_root: str = "extensions/wordflow_kernel") -> dict[str, Any]:
    """PLUGIN = enchufe ficha.v2. No load side-effects beyond validate."""
    try:
        from extensions.wordflow.engine.enchufe_gate import validate_ficha
    except ImportError:
        try:
            from wordflow.engine.enchufe_gate import validate_ficha
        except ImportError:
            return {"ok": False, "error": "ENCHUFE_MISSING", "invoked": False}
    ficha_path = _resolve_ficha(module_root)
    if not ficha_path.is_file():
        return {
            "ok": False,
            "invoked": True,
            "error": "FICHA_NOT_ON_DISK",
            "path": str(ficha_path),
            "declared": _PHASE_PATHS["plugin"],
        }
    data = json.loads(ficha_path.read_text(encoding="utf-8"))
    result = validate_ficha(data)
    result["invoked"] = True
    result["path"] = str(ficha_path)
    return result


def _pack(instance_id: str | None) -> dict[str, Any]:
    if not instance_id:
        return {"ok": False, "invoked": False, "error": "NO_INSTANCE"}
    try:
        from extensions.wordflow_kernel.context_pack import run_context_pack
    except ImportError:
        try:
            from .context_pack import run_context_pack
        except ImportError:
            return {"ok": False, "invoked": False, "error": "CONTEXT_PACK_MISSING"}
    try:
        return {**run_context_pack(instance_id), "invoked": True}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "invoked": True, "error": str(exc)}


def ingest(input_block: dict[str, Any] | None, **kwargs: Any) -> dict[str, Any]:
    """convert → compile → classify → locate_phase → plugin → optional apply_and_push.

    FAIL-closed: plugin.ok must be True.
    apply=True writes phase_plan.json.
    dest+account_id+files → github_deploy.apply_and_push (0% LLM).
    hops_ok requires every hop ok (not just invoked).
    """
    from .git_apply import push_if_dest

    converted = convert(
        input_block,
        **{k: v for k, v in kwargs.items() if k in ("use_sdpa", "branch", "max_context")},
    )
    text = ""
    if isinstance(converted, dict):
        text = str((converted.get("normalized") or {}).get("text") or "")
    compiled = _compile(input_block, converted)
    classified = _classify(text)
    phase = locate_phase(text)
    plugin = attach_plugin()
    pack = _pack(kwargs.get("instance_id"))
    loc = locate("inbox")
    plan = {"ok": False, "wrote": False, "reason": "locate_only", "git_apply": False}
    if kwargs.get("apply"):
        dest = kwargs.get("plan_path") or str(Path.cwd() / "phase_plan.json")
        plan = apply_phase_plan(phase, dest)
    git = push_if_dest(input_block, kwargs, phase)
    hops = [compiled, classified, phase, plugin]
    hops_ok = bool(converted.get("ok")) and all(bool(h.get("ok")) for h in hops)
    ok = bool(converted.get("ok") and compiled.get("invoked") and plugin.get("ok"))
    return {
        "ok": ok,
        "converted": converted,
        "contract": compiled,
        "classification": classified,
        "phase": phase,
        "plugin": plugin,
        "context_pack": pack,
        "locate": loc,
        "phase_plan": plan,
        "git": git,
        "invoked": {
            "input_compiler": bool(compiled.get("invoked")),
            "task_classifier": bool(classified.get("invoked")),
            "locate_phase": True,
            "enchufe_plugin": bool(plugin.get("invoked")),
            "context_pack": bool(pack.get("invoked")),
            "apply_push": not bool(git.get("skipped")),
        },
        "wrote": bool(plan.get("wrote")),
        "git_apply": bool(git.get("git_apply")),
        "hops_ok": hops_ok,
    }


if __name__ == "__main__":
    loc = locate()
    assert loc["ok"] and "reception" in loc["path"]
    missing_ok = convert(None)
    assert "ok" in missing_ok
    out = ingest({"raw_text": "objective: wire kernel\nsuccess: ingest invokes compiler"})
    assert out["invoked"]["input_compiler"] is True
    print("ok", loc["path"], out["invoked"], "plugin", out["plugin"].get("ok"))
