from loops.agent_adapter import AgentAdapter, CallableAgent, AgentExecResult
from loops.phase_handlers import make_default_handlers
from loops.phases import PhaseRunner


def test_mhytos_parallel_ok():
    ad = AgentAdapter()
    ad.register_runtime(CallableAgent(
        "coder", ["code_generation"],
        lambda c, p: AgentExecResult(ok=True, output={"phase": p.get("mhytos_phase"), "cap": c}),
    ))
    runner = PhaseRunner(handlers=make_default_handlers(ad))
    results, verdict = runner.run({
        "run_id": "R", "capability": "code_generation", "strategy": "parallel",
    })
    assert verdict.ok
    ejec = next(r for r in results if r.phase == "ejecutar")
    assert ejec.ok and ejec.output.get("strategy") == "parallel"
    assert "investigation" in (ejec.output.get("mhytos") or {})
