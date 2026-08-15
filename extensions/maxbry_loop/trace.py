class TraceEngine:
    def diff(self, before: dict, after: dict) -> dict:
        changes = {}
        bt = before.get("tasks", {})
        at = after.get("tasks", {})
        added = sorted(set(at) - set(bt))
        removed = sorted(set(bt) - set(at))
        status = {}
        for k in set(bt) & set(at):
            if bt[k].get("status") != at[k].get("status"):
                status[k] = {"from": bt[k].get("status"), "to": at[k].get("status")}
        if added:
            changes["tasks_added"] = added
        if removed:
            changes["tasks_removed"] = removed
        if status:
            changes["status_changes"] = status
        if before.get("completion_score") != after.get("completion_score"):
            changes["completion_score"] = {
                "from": before.get("completion_score"),
                "to": after.get("completion_score"),
            }
        return changes
