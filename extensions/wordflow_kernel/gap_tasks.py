from .models import TaskSpec, uid


class GapTaskCompiler:
    """GAP → TaskSpec. Auditor never writes code; only emits tasks."""

    def compile(self, report, workspace_id: str):
        tasks = []
        for gap in report.gaps:
            tasks.append(
                TaskSpec(
                    task_id=uid("task"),
                    gap_id=gap.gap_id,
                    objective=gap.recommendation or f"Resolve: {gap.requirement}",
                    target="repository",
                    acceptance=(
                        "gap no longer reported as MISSING/PARTIAL",
                        "validator passes",
                        "evidence packet generated",
                    ),
                    workspace_id=workspace_id,
                )
            )
        return tasks
