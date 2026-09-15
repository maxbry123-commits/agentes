
import json
import traceback
from pathlib import Path
from dataclasses import asdict
from typing import Dict, Any, Tuple, List

from model import LLM
from log import AgentLogger
from monitor import Monitor
from prompt.system_prompt import sys_memory_prompt_template
from utils import remove_accessibility_tree_in_the_history, remove_browser_state_in_the_history, \
    create_message, deep_update, dict_to_outline_str, pretty_print_trajectory, remove_python_code_in_the_history

class MemoryManager:
    def __init__(self, memory_dir: str, logger: AgentLogger, output_dir: Path, sys_prompt_template: str, tool_schema_texts: str, use_memory: bool = True):
        self.memory_dir = Path(memory_dir)
        self.logger = logger
        self.output_dir: Path = output_dir
        self.sys_prompt_template = sys_prompt_template
        self.tool_schema_texts = tool_schema_texts
        self.use_memory = use_memory

        self.history: List[dict] = []

        self.tool_enhance_dict: Dict[str, Any] = self._load_memory(self.memory_dir / "tool_memory.json")
        self.application_enhance_dict: Dict[str, Any] = self._load_memory(self.memory_dir / "procedural_memory.json")
        self.methodology_enhance_dict: Dict[str, Any] = self._load_memory(self.memory_dir / "strategic_memory.json")

        self.app_guide_str = dict_to_outline_str(self.application_enhance_dict)
        self.metho_guide_str = dict_to_outline_str(self.methodology_enhance_dict)

        def _memory_loading_log(items: List[tuple]):
            for content, title in items:
                self.logger.log_task(str(content), subtitle="LOADING······", title=f"Load {title} Memory")

        _memory_loading_log([
            (self.tool_enhance_dict, "Tool"),
            (self.app_guide_str, "Application"),
            (self.metho_guide_str, "Methodology")
        ])

        self.update_system_prompt()

    @staticmethod
    def _load_memory(memory_path: Path) -> dict:
        try:
            with open(memory_path, "r", encoding="utf-8") as f:
                text = f.read()
                if not text.strip():
                    print(f"Warning: {memory_path} is empty.")
                    return {}
                try:
                    return json.loads(text)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON in {memory_path}: {e}")
                    traceback.print_exc()
                    return {}
        except FileNotFoundError:
            print(f"File not found: {memory_path}")
            return {}
        except Exception as e:
            print(f"Unexpected error reading {memory_path}: {e}")
            traceback.print_exc()
            return {}

    @staticmethod
    def _save_memory(memory_path: Path, data: dict):
        try:
            with open(memory_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save memory to {memory_path}: {e}")
            traceback.print_exc()

    def update_system_prompt(self):
        if self.use_memory:
            memory = sys_memory_prompt_template.format(
                methodology=self.metho_guide_str,
                guidance=self.app_guide_str
            )
        else:
            memory = sys_memory_prompt_template.format(
                methodology="",
                guidance="",
            )
            self.logger.log_task("Pass the memory load step", subtitle="WARNING···", title="use_memory set to False")

        system_prompt = self.sys_prompt_template.format(
            memory=memory,
            tools=self.tool_schema_texts
        )
        if not self.history or self.history[0]["role"] != "system":
            self.history.insert(0, create_message("system", system_prompt))
        else:
            self.history[0] = create_message("system", system_prompt)

    def add_turn(self, user_message: dict, assistant_message: dict):
        self.history.extend([user_message, assistant_message])

    def add_traj(self, trajectory: List[dict]):
        self.history.extend(trajectory)

    def rm_traj_by_length(self, length: int, offset: int = 0):
        if length > 0:
            if offset == 0:
                self.history = self.history[:-length]
            else:
                self.history = self.history[:-(offset + length)] + self.history[-offset:]

    def add_message(self, role: str, content: str):
        self.history.append(create_message(role, content))

    def get_history(self) -> List[dict]:
        return self.history

    @staticmethod
    def trim_traj(
            traj: list,
            preserve_last: int = 0,
            axtree: bool = True,
            state: bool = True,
            python: bool = True,
    ):
        """
        Clear all conversation turns (user+assistant) from the end of the trace in reverse order, keeping the last preserve_last turn.
        """
        if not isinstance(traj, list) or len(traj) < 2:
            return

        skip = preserve_last * 2
        start = len(traj) - 1 - skip
        if start < 1:
            return

        i = start
        while i >= 1:
            msg_a = traj[i]
            msg_u = traj[i - 1]

            assert msg_u.get("role") == "user", f"role mismatch at index {i - 1}: expected user"
            assert msg_a.get("role") == "assistant", f"role mismatch at index {i}: expected assistant"

            text_u = msg_u["content"][0]["text"]
            if axtree:
                text_u = remove_accessibility_tree_in_the_history(text_u)
            if state:
                text_u = remove_browser_state_in_the_history(text_u)
            msg_u["content"][0]["text"] = text_u

            text_a = msg_a["content"][0]["text"]
            if python:
                text_a = remove_python_code_in_the_history(text_a)
            msg_a["content"][0]["text"] = text_a

            i -= 2

    def update_and_save_app_memory(self, new_conclusion: dict):
        self.logger.log_task(str(new_conclusion), subtitle="UPDATING······", title="Update App Memory")
        deep_update(self.application_enhance_dict, new_conclusion)
        self.app_guide_str = dict_to_outline_str(self.application_enhance_dict)
        self._save_memory(self.memory_dir / "procedural_memory.json", self.application_enhance_dict)

    def save_all_memory_to_disk(self):
        self._save_memory(self.memory_dir / "tool_memory.json", self.tool_enhance_dict)
        self._save_memory(self.memory_dir / "procedural_memory.json", self.application_enhance_dict)
        self._save_memory(self.memory_dir / "strategic_memory.json", self.methodology_enhance_dict)

    def save_run_artifacts(self, monitor: Monitor):
        output_dir = self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        history_output_path = output_dir / "history.txt"
        history_str = pretty_print_trajectory(self.history, show_full_content=True, print_to_terminal=False)
        with history_output_path.open("w", encoding="utf-8") as f:
            f.write(history_str)

        overall_state_output_path = output_dir / "overall_state.json"
        overall_state = {
            "monitor_state": asdict(monitor),
            "enhance_dicts": {
                "tool_enhance_dict": self.tool_enhance_dict,
                "application_enhance_dict": self.application_enhance_dict,
                "methodology_enhance_dict": self.methodology_enhance_dict
            }
        }
        with overall_state_output_path.open("w", encoding="utf-8") as f:
            json.dump(overall_state, f, indent=4, ensure_ascii=False)

        with open(output_dir / "num_calls.txt", "w", encoding="utf-8") as f:
            f.write(str({
                "num_calls": LLM.NUM_CALLS,
                "prompt_tokens": LLM.PROMPT_TOKENS,
                "completion_tokens": LLM.COMPLETION_TOKENS,
                "max_tokens": LLM.MAX_TOKENS
            }))

