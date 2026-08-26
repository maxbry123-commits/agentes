from .models import Plan, LoopState, StepResult


def make_default_handlers():
    """Safe deterministic defaults. Replace with real kernel adapters as needed."""

    def admit(p, s):
        return StepResult("PASS", {"mission_id": p.mission_id})

    def lock_goals(p, s):
        return StepResult(
            "PASS", {"goal_ids": [g.id for g in p.goals], "goal_count": len(p.goals)}
        )

    def load_context(p, s):
        return StepResult("PASS", {"context": "kernel_context_loaded"})

    def audit(p, s):
        return StepResult("PASS", {"audit": "pre_execution_pass"})

    def acquire(p, s):
        return StepResult("PASS", {"resources": "available_only"})

    def plan(p, s):
        return StepResult("PASS", {"steps": p.steps})

    def execute(p, s):
        return StepResult("PASS", {"execution": "handler_completed"})

    def validate(p, s):
        return StepResult("PASS", {"validator": "pass"})

    def refute(p, s):
        return StepResult("PASS", {"refutation": "no_blocking_counterexample"})

    def repair(p, s):
        return StepResult("PASS", {"repair": "not_required"})

    def verify(p, s):
        return StepResult("PASS", {"verification": "evidence_consistent"})

    def close(p, s):
        return StepResult("PASS", {"closed": True})

    return dict(
        zip(
            [
                "ADMIT",
                "LOCK_GOALS",
                "LOAD_CONTEXT",
                "AUDIT",
                "ACQUIRE",
                "PLAN",
                "EXECUTE",
                "VALIDATE",
                "REFUTE",
                "REPAIR",
                "VERIFY",
                "CLOSE",
            ],
            [
                admit,
                lock_goals,
                load_context,
                audit,
                acquire,
                plan,
                execute,
                validate,
                refute,
                repair,
                verify,
                close,
            ],
        )
    )
