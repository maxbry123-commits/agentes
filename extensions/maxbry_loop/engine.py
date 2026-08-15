from copy import deepcopy
from .models import State, Event, now
from .integrity import validate, ready_tasks
from .gaps import detect_gaps, append_gap_tasks
from .trace import TraceEngine


class Engine:
    def __init__(self, state, store, model, config):
        self.state = state
        self.store = store
        self.model = model
        self.config = config
        self.trace = TraceEngine()

    def bootstrap(self):
        validate(self.state)
        self.store.save(self.state)

    def completion(self):
        tasks = list(self.state.tasks.values())
        if not tasks:
            return 0.0
        done = sum(t.status == "done" for t in tasks)
        blockers = sum(t.status == "blocked" for t in tasks)
        score = done / len(tasks)
        if blockers:
            score *= 0.8
        self.state.completion_score = round(score, 4)
        self.state.blockers = [t.id for t in tasks if t.status == "blocked"]
        return self.state.completion_score

    def iteration(self):
        self.state.iteration += 1
        before = deepcopy(self.state.to_dict())
        self.store.event(
            Event(
                "iteration_started",
                {"workflow_version": self.state.workflow_version},
                self.state.iteration,
            )
        )
        validate(self.state)
        tasks = ready_tasks(self.state)

        if not tasks:
            gaps = detect_gaps(self.state.goal, self.state)
            added = append_gap_tasks(
                self.state,
                gaps,
                self.config["loop"].get("max_new_tasks_per_iteration", 10),
            )
            if added:
                self.store.event(
                    Event(
                        "tasks_added",
                        {"ids": [t.id for t in added]},
                        self.state.iteration,
                    )
                )
            else:
                self.completion()
                self.store.event(
                    Event(
                        "no_ready_work",
                        {"score": self.state.completion_score},
                        self.state.iteration,
                    )
                )
                self.store.save(self.state)
                return
            tasks = ready_tasks(self.state)

        for task in tasks:
            task.attempts += 1
            result = self.model.execute(task, self.state.goal)
            task.result = result.get("result", "")
            task.evidence = list(result.get("evidence", []))
            task.status = result.get("status", "blocked")
            task.updated_at = now()
            self.store.event(
                Event(
                    "task_completed" if task.status == "done" else "task_state_changed",
                    {"task_id": task.id, "status": task.status, "evidence": task.evidence},
                    self.state.iteration,
                )
            )

        gaps = detect_gaps(self.state.goal, self.state)
        added = append_gap_tasks(
            self.state,
            gaps,
            self.config["loop"].get("max_new_tasks_per_iteration", 10),
        )
        if added:
            self.store.event(
                Event(
                    "improvement_tasks_added",
                    {"ids": [t.id for t in added]},
                    self.state.iteration,
                )
            )

        validate(self.state)
        score = self.completion()
        after = self.state.to_dict()
        changes = self.trace.diff(before, after)
        self.store.event(
            Event(
                "traceability",
                {
                    "changes": changes,
                    "workflow_version": self.state.workflow_version,
                    "completion_score": score,
                    "blockers": self.state.blockers,
                },
                self.state.iteration,
            )
        )
        if self.config["loop"].get("checkpoint_every_iteration", True):
            self.store.checkpoint(self.state)
        self.store.save(self.state)

    def run(self):
        self.bootstrap()
        max_iter = self.config["loop"].get("max_iterations", 50)
        threshold = self.config["loop"].get("completion_threshold", 0.98)
        for _ in range(max_iter):
            self.iteration()
            score = self.completion()
            if score >= threshold and not self.state.blockers:
                self.store.event(
                    Event("goal_completed", {"score": score}, self.state.iteration)
                )
                self.store.save(self.state)
                return self.state
        self.store.event(
            Event(
                "budget_exhausted",
                {"score": self.state.completion_score, "iteration": self.state.iteration},
                self.state.iteration,
            )
        )
        self.store.save(self.state)
        return self.state
