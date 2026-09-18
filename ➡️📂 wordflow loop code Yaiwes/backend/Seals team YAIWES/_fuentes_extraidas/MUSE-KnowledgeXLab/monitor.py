from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

@dataclass
class Reflection:
    analysis: str = ""
    check_report: str = ""
    time_used: float = 0

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

@dataclass
class SubTask:
    name: str
    goal: str
    index: int = -1   # `-1` indicates not executed
    finish: bool = False
    trajectory: List[dict] = field(default_factory=list)
    reflect_trajectory: List[dict] = field(default_factory=list)
    reflection: Reflection = field(default_factory=Reflection)
    try_times: int = 0

    def set_index(self, index: int):
        self.index = index

    @classmethod
    def from_dict(cls, data: dict):
        reflection = Reflection.from_dict(data.get("reflection", {}))
        return cls(
            name=data.get("name", ""),
            goal=data.get("goal", ""),
            index=data.get("index", -1),
            finish=data.get("finish", False),
            trajectory=data.get("trajectory", []),
            reflect_trajectory=data.get("reflect_trajectory", []),
            reflection=reflection,
            try_times=data.get("try_times", 0),
        )

@dataclass
class AgentException:
    subtask_limit_exceeded: int = 0
    memory_exception: List[Dict[str, str]] = field(default_factory=list)

    def is_exception(self):
        return self.subtask_limit_exceeded > 0 or len(self.memory_exception) > 0

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            subtask_limit_exceeded=data.get("subtask_limit_exceeded", 0),
            memory_exception=data.get("memory_exception", []),
        )

@dataclass
class ToolStat:
    calls: int = 0
    modified: int = 0
    errors: int = 0

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            calls=data.get("calls", 0),
            modified=data.get("modified", 0),
            errors=data.get("errors", 0),
        )

@dataclass
class Monitor:
    num_actions: int = 0
    time_used: float = 0.0
    tool_call: Dict[str, ToolStat] = field(default_factory=dict)
    done_subtasks: List[SubTask] = field(default_factory=list)
    exception: AgentException = field(default_factory=AgentException)

    def add_actions(self, n: int):
        self.num_actions += n

    def update_time(self, time: float):
        self.time_used = time

    def inc_subtask_limit_exceeded(self):
        self.exception.subtask_limit_exceeded += 1

    def add_memory_update_exception(self, where: str, msg: str):
        self.exception.memory_exception.append({where: msg})

    def init_tool(self, name: str):
        self.tool_call[name] = ToolStat()

    def _exist_tool(self, name: str) -> bool:
        if name in self.tool_call:
            return True
        print(f"[SYSTEM ERROR: Can't update tool stat: tool `{name}` not found.]")
        return False

    def inc_tool_call(self, name: str):
        if self._exist_tool(name):
            self.tool_call[name].calls += 1

    def inc_tool_modified(self, name: str):
        if self._exist_tool(name):
            self.tool_call[name].modified += 1

    def inc_tool_error(self, name: str):
        if self._exist_tool(name):
            self.tool_call[name].errors += 1

    def add_done_subtask(self, subtask: SubTask):
        assert subtask.index != -1
        self.done_subtasks.append(subtask)

    def get_done_subtask_for_reflection(self):
        return [{
            "name": x.name,
            "index": x.index,
            "goal": x.goal,
            "finish": x.finish,
            "check_report": x.reflection.check_report
        } for x in self.done_subtasks]

    @property
    def subtasks_used(self):
        return len(self.done_subtasks)

    @classmethod
    def from_dict(cls, data: dict):
        raw_tool_call = data.get("tool_call", {})
        tool_call: Dict[str, ToolStat] = {}
        for name, info in raw_tool_call.items():
            if isinstance(info, ToolStat):
                tool_call[name] = info
            elif isinstance(info, dict):
                tool_call[name] = ToolStat.from_dict(info)
            else:
                tool_call[name] = ToolStat()

        done_subtasks = [SubTask.from_dict(s) for s in data.get("done_subtasks", [])]
        exception = AgentException.from_dict(data.get("exception", {}))

        return cls(
            num_actions=data.get("num_actions", 0),
            time_used=data.get("time_used", 0.0),
            tool_call=tool_call,
            done_subtasks=done_subtasks,
            exception=exception,
        )