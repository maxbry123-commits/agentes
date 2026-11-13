"""Wave2 ops · adjunta Research/Opportunity/Watchdog/Genome/Worker al controller."""
from __future__ import annotations
from pathlib import Path
from typing import Any

def attach_wave2(ctl: Any, sources_dir: str = "evolution/sources") -> Any:
    from .research.registry import ResearchRegistry
    from .opportunity.engine import OpportunityEngine
    from .watchdog.monitor import Watchdog
    from .genome.compatibility import CompatibilityGenome
    from .workers.code_worker import CodeWorker

    if not hasattr(ctl, "research_registry"):
        ctl.research_registry = ResearchRegistry(str(Path(sources_dir).parent / "research_registry.json"))
    if not hasattr(ctl, "opportunity"):
        ctl.opportunity = OpportunityEngine()
    if not hasattr(ctl, "watchdog"):
        ctl.watchdog = Watchdog(fail_threshold=3)
        ctl.watchdog.set_rollback_handler(lambda mid: ctl.ledger.mark_rollback(mid))
    if not hasattr(ctl, "genome_engine"):
        ctl.genome_engine = CompatibilityGenome()
    if not hasattr(ctl, "code_worker"):
        ctl.code_worker = CodeWorker()

    if not hasattr(ctl, "research"):
        def research(query: str = "", *, local=None):
            found = []
            if query:
                found.extend(c.to_dict() for c in ctl.research_registry.parse_query_hints(query))
            if local:
                for ident, path in local.items():
                    found.append(ctl.research_registry.add_local(ident, path).to_dict())
            return found
        ctl.research = research

    if not hasattr(ctl, "research_and_evolve"):
        def research_and_evolve(query: str = "", *, local=None):
            cands = ctl.research(query, local=local)
            results = []
            for c in cands:
                kw = ctl.research_registry.to_evolve_kwargs(c)
                path = kw.pop("path", None)
                r = ctl.evolve_path(path, **kw)
                results.append(r.to_dict() if hasattr(r, "to_dict") else r)
                ctl.watchdog.on_evolve_result(results[-1])
            return results
        ctl.research_and_evolve = research_and_evolve

    if not hasattr(ctl, "safe_invoke"):
        def safe_invoke(capability: str, payload=None):
            out = ctl.registry.invoke(capability, payload)
            entry = ctl.registry.resolve(capability)
            plugin_id = entry.plugin_id if entry else ""
            ev = ctl.watchdog.on_invoke_result(capability, out, plugin_id=plugin_id)
            if ev and ev.action == "rollback_propose":
                for e in reversed(ctl.ledger.list_entries()):
                    if e.get("plugin_id") == plugin_id and not e.get("rolled_back"):
                        ctl.watchdog.propose_rollback(e["mutation_id"])
                        out = dict(out); out["watchdog_rollback"] = e["mutation_id"]
                        break
            return out
        ctl.safe_invoke = safe_invoke

    if not hasattr(ctl, "scan_opportunities"):
        def scan_opportunities(task_hints=None):
            return [o.to_dict() for o in ctl.opportunity.scan_registry(ctl.registry.list_capabilities(), task_hints=task_hints)]
        ctl.scan_opportunities = scan_opportunities

    # post-process evolve_path: genome + worker if package exists
    if not getattr(ctl, "_wave2_evolve_wrapped", False):
        _orig = ctl.evolve_path
        def evolve_path_wrapped(*args, **kwargs):
            r = _orig(*args, **kwargs)
            d = r.to_dict() if hasattr(r, "to_dict") else dict(r)
            # worker on package
            if d.get("ok") and d.get("package_path") and Path(d["package_path"]).exists():
                wr = ctl.code_worker.fill_adapter(
                    d["package_path"],
                    plugin_id=d.get("plugin_id") or "plugin",
                    capabilities=d.get("registered") or [],
                    mode="deterministic",
                )
                if hasattr(r, "worker"):
                    r.worker = wr.to_dict()
                d["worker"] = wr.to_dict()
            # genome
            gr = ctl.genome_engine.evaluate(
                after={"registered": d.get("registered") or [], "fingerprint": (d.get("evo_ir") or {}).get("fingerprint")},
                simulation=d.get("simulation") or {},
                license_verdict=(d.get("license") or {}).get("veredicto", "PASS"),
                preserved_cognitive=(d.get("plan") or {}).get("preserved_cognitive"),
                subordinated_control=(d.get("plan") or {}).get("subordinated_control"),
            )
            if hasattr(r, "genome"):
                r.genome = gr.to_dict()
            d["genome"] = gr.to_dict()
            if gr.decision == "REJECT" and hasattr(r, "ok"):
                r.ok = False
                r.phase = "GENOME_REJECT"
            # opportunities
            opps = ctl.scan_opportunities()
            if hasattr(r, "opportunities"):
                r.opportunities = opps
            d["opportunities"] = opps
            return r
        ctl.evolve_path = evolve_path_wrapped
        ctl._wave2_evolve_wrapped = True
    return ctl
