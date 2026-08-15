from .models import Task


class IntegrityError(Exception):
    pass


def validate(state):
    errors = []
    ids = set(state.tasks)
    for tid, t in state.tasks.items():
        if tid != t.id:
            errors.append(f"id mismatch: {tid} != {t.id}")
        for dep in t.depends_on:
            if dep not in ids:
                errors.append(f"{tid}: missing dependency {dep}")
        if tid in t.depends_on:
            errors.append(f"{tid}: self dependency")
    visiting, visited = set(), set()

    def dfs(n):
        if n in visiting:
            errors.append(f"dependency cycle at {n}")
            return
        if n in visited:
            return
        visiting.add(n)
        for dep in state.tasks[n].depends_on:
            if dep in state.tasks:
                dfs(dep)
        visiting.remove(n)
        visited.add(n)

    for tid in list(state.tasks):
        dfs(tid)
    if errors:
        raise IntegrityError("; ".join(errors))
    return True


def ready_tasks(state):
    ready = []
    for t in state.tasks.values():
        if t.status not in ("pending", "ready"):
            continue
        deps_ok = all(
            state.tasks[d].status == "done" for d in t.depends_on if d in state.tasks
        )
        if deps_ok:
            ready.append(t)
    ready.sort(key=lambda x: (-x.priority, x.created_at))
    return ready
