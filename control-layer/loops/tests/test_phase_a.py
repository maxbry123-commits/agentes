"""Salida A: ejecutar despacha agente real via adapter"""
from loops.agent_adapter import AgentAdapter, CallableAgent, AgentExecResult
from loops.phase_handlers import make_default_handlers
from loops.phases import PhaseRunner
from loops.engine import LoopEngine
from loops.contracts.types import LoopContext
from loops.policy.engine import PolicyEngine


def test_ejecutar_dispatches_agent():
    ad = AgentAdapter()

    def work(cap, payload):
        return AgentExecResult(ok=True, output={"code": "print(1)", "cap": cap}, tokens_used=10)

    ad.register_runtime(CallableAgent("coder", ["code_generation"], work))
    handlers = make_default_handlers(ad)
    runner = PhaseRunner(handlers=handlers)
    results, verdict = runner.run({"run_id": "R1", "capability": "code_generation"})
    assert verdict.ok
    by = {r.phase: r for r in results}
    assert by["ejecutar"].ok
    assert by["ejecutar"].output.get("resolved_by") == "coder"
    assert by["ejecutar"].output["agent_output"]["code"] == "print(1)"


def test_engine_with_handlers_closes():
    ad = AgentAdapter()
    ad.register_runtime(CallableAgent(
        "coder", ["code_generation"],
        lambda c, p: AgentExecResult(ok=True, output={"done": True}),
    ))
    eng = LoopEngine(
        policy=PolicyEngine([
            {"id": "c", "when": {"phase_outcome": "validation_passed", "goal_complete": True},
             "action": "CLOSE", "reason": "ok"}
        ]),
        phase_handlers=make_default_handlers(ad),
    )
    ctx = LoopContext(
        run_id="R-a", loop_id="L", project_id="P", agent_id="coder",
        task_id="T", goal_id="G", created_at="t", updated_at="t",
        inputs={"capability": "code_generation"},
    )
    # pass capability via run context — handlers read ctx dict from phases.run
    # engine passes run_id/iteration only; inject via phase context by custom handlers already using default_capability
    r = eng.run_iteration(ctx, goal_complete=True)
    assert r.closed
