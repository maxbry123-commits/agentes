from __future__ import annotations

import yaiwes_real_workflow_chain_v61 as v61

base = v61.base


def _source_contract_v62(comp, profile):
    manifest = base._manifest(comp)
    by_path = {x["path"]: x for x in manifest.get("files", [])}
    item = by_path.get(profile["path"])
    if item is None:
        raise RuntimeError(f"source not audited: {profile['path']}")
    if item["decision"] not in {"KEEP_UNCHANGED", "RESTORE_BENIGN"}:
        raise RuntimeError(f"unsafe source decision: {item['decision']}")

    source = comp / "code" / profile["path"]
    if not source.is_file():
        raise RuntimeError(f"missing active source: {profile['path']}")
    text = source.read_text(encoding="utf-8")
    active_sha = base._sha_text(text)
    if active_sha != item["active_sha256"]:
        raise RuntimeError("active source SHA does not match audited manifest")

    # A RESTORE_BENIGN record can retain a historical quarantine pointer from
    # the surgical audit.  We never read or import that historical copy.  The
    # active source is eligible only when it is byte-identical to the audited
    # original SHA.
    if item["decision"] == "RESTORE_BENIGN" and active_sha != item["original_sha256"]:
        raise RuntimeError("restored benign active source is not byte-identical to original")
    if item["decision"] == "KEEP_UNCHANGED" and item.get("quarantine"):
        raise RuntimeError("unchanged source unexpectedly points at quarantine")

    return {
        "decision": item["decision"],
        "active_sha256": active_sha,
        "original_sha256": item["original_sha256"],
        "source": source,
        "text": text,
        "historical_quarantine_pointer_ignored": bool(item.get("quarantine")),
    }


base._source_contract = _source_contract_v62


if __name__ == "__main__":
    state_root = base.ROOT / "🏈 cancha deportiva de fútbol" / ".yaiwes_v6_runtime"
    report = base.run_swarm(
        state_root,
        "yaiwes-v62-e2e",
        {"mode": "benign-research-persistence", "contract": "active-source-sha-only"},
    )
    print({
        "components": report["components"],
        "real_internal_workflows_executed": report["real_internal_workflows_executed"],
        "source_unavailable_closures": report["source_unavailable_closures"],
        "status": report["status"],
    })
