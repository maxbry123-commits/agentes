"""4 simulaciones de auditoría · buscan errores · multiagente nativo"""
from loops.agent_adapter import AgentAdapter, CallableAgent, AgentExecResult
from loops.catalog import catalog_size, generate_catalog
from loops.contracts.capability import CapabilityRequest
from loops.contracts.types import LoopContext
from loops.engine import LoopEngine
from loops.mhytos import MHYTOSExecutor, PhaseOut
from loops.policy.engine import PolicyEngine
from loops.simulator import LoopSimulator, ChaosMonkey
from loops.budget_pool import BudgetPool
from loops.similarity import jaccard, rank_similar


def _ctx(run_id="R-a", agent_id="A1", **kw):
    b = dict(
        run_id=run_id, loop_id="L01", project_id="P1", agent_id=agent_id,
        task_id="T1", goal_id="G1", created_at="t", updated_at="t",
        budgets={"retry_budget": 2}, recovery_state={"repair_count": 0},
    )
    b.update(kw)
    return LoopContext(**b)


def test_sim1_happy_and_multiagent_isolation():
    """Sim1: dos agentes distinto agent_id no comparten estado."""
    eng = LoopEngine(policy=PolicyEngine([
        {"id": "c", "when": {"phase_outcome": "validation_passed", "goal_complete": True},
         "action": "CLOSE", "reason": "ok"}
    ]))
    r1 = eng.run_iteration(_ctx("R1", "agent-temporal"), goal_complete=True)
    r2 = eng.run_iteration(_ctx("R2", "agent-openclaw"), goal_complete=True)
    assert r1.closed and r2.closed
    assert r1.ctx.agent_id != r2.ctx.agent_id
    assert r1.ctx.run_id != r2.ctx.run_id


def test_sim2_adapter_any_agent():
    """Sim2: adapter despacha a temporal y coder sin cambiar engine."""
    ad = AgentAdapter()

    def temporal_fn(cap, payload):
        return AgentExecResult(ok=True, output={"source": "temporal", "cap": cap})

    def coder_fn(cap, payload):
        return AgentExecResult(ok=True, output={"source": "coder", "cap": cap})

    ad.register_runtime(CallableAgent("temporal", ["research", "planning"], temporal_fn), priority=10)
    ad.register_runtime(CallableAgent("coder", ["code_generation"], coder_fn), priority=10)
    r1 = ad.dispatch(CapabilityRequest("1", "R", "research", "t"), {})
    r2 = ad.dispatch(CapabilityRequest("2", "R", "code_generation", "t"), {})
    assert r1.ok and r1.output["source"] == "temporal"
    assert r2.ok and r2.output["source"] == "coder"


def test_sim3_chaos_and_stall():
    """Sim3: chaos dup + simulator paths."""
    sim = LoopSimulator()
    results = sim.run_all()
    assert len(results) == 4
    assert results[0].ok  # happy
    eng = LoopEngine.with_default_policy()
    ctx = _ctx("R-chaos", idempotency_key="dup")
    a, b = ChaosMonkey().duplicate_iteration(eng, ctx)
    assert b.cache_hit


def test_sim4_mhytos_catalog_pool_similarity():
    """Sim4: P3 pieces."""
    assert catalog_size() == 1080
    assert len(generate_catalog(limit=10)) == 10

    def ok_handler(phase, ctx):
        return PhaseOut(phase=phase, ok=True, output={phase: True})

    mh = MHYTOSExecutor(handlers={p: ok_handler for p in [
        "investigation", "planning", "execution", "improvements", "review", "strategy"
    ]})
    outs = mh.run({}, parallel=False)
    assert mh.all_ok(outs)

    pool = BudgetPool("fase")
    pool.add("r1")
    pool.add("r2")
    pool.rebalance()

    assert jaccard("code generation python", "python code gen") > 0.3
    ranked = rank_similar("loop stall recovery", [("a", "stall recovery loop"), ("b", "image cat")])
    assert ranked[0][0] == "a"
