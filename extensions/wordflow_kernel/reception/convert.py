"""Kernel LINK to Wordflow reception convert + locate.

Source of inbox files:
  extensions/wordflow/reception/
This module does not duplicate convert logic. It imports it fail-closed.
"""
from __future__ import annotations

from typing import Any

DEFAULT_MAX_CONTEXT = 20_000_000

_RECEPTION_DIR = "extensions/wordflow/reception"
_KERNEL_RECEPTION = "extensions/wordflow_kernel/reception"


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
    """Where reception artifacts live on GitHub=truth."""
    kind = (kind or "inbox").strip().lower()
    paths = {
        "inbox": f"{_RECEPTION_DIR}/RECEPTION_agentes.md",
        "template": f"{_RECEPTION_DIR}/RECEPTION_TEMPLATE.md",
        "links": f"{_RECEPTION_DIR}/KNOWLEDGE_RECEPTION_LINKS.md",
        "guide": f"{_RECEPTION_DIR}/advanced_engineering_code_standard_guia_maestra.md",
        "convert": f"{_RECEPTION_DIR}/convert.py",
        "kernel": _KERNEL_RECEPTION,
        "motor": "extensions/wordflow/motors/kernel_ext/motor.py",
    }
    return {
        "ok": True,
        "kind": kind,
        "path": paths.get(kind, paths["inbox"]),
        "catalog": paths,
        "url_inbox": "https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow/reception",
        "url_kernel": "https://github.com/maxbry123-commits/agentes/tree/main/extensions/wordflow_kernel/reception",
    }


def ingest(input_block: dict[str, Any] | None, **kwargs: Any) -> dict[str, Any]:
    """Kernel entry: convert then attach locate metadata."""
    converted = convert(input_block, **kwargs)
    loc = locate("inbox")
    return {
        "ok": bool(converted.get("ok")),
        "converted": converted,
        "locate": loc,
        "next": ["wordflow.engine.input_compiler", "wordflow_kernel.context_pack"],
    }


if __name__ == "__main__":
    loc = locate()
    assert loc["ok"] and "reception" in loc["path"]
    missing_ok = convert(None)
    assert "ok" in missing_ok
    print("ok", loc["path"], missing_ok.get("error") or missing_ok.get("ok"))
