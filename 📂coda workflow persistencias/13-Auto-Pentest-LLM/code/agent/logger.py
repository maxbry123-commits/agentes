import json
import os
import time
from datetime import datetime
from typing import Dict, Any, List

class SessionLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f"session_{self.session_id}.json")
        self.md_file = os.path.join(log_dir, f"session_{self.session_id}.md")
        self.history: List[Dict[str, Any]] = []
        
        self._init_md_log()

    def _init_md_log(self):
        with open(self.md_file, "w") as f:
            f.write(f"# Pentest Session: {self.session_id}\n\n")

    def log_step(self, step_type: str, content: Any, meta: Dict[str, Any] = None):
        """
        Log a single step in the agent's execution.
        step_type: 'action', 'output', 'error', 'thought'
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": step_type,
            "content": content,
            "meta": meta or {}
        }
        self.history.append(entry)
        self._save_json()
        self._append_md(entry)

    def _save_json(self):
        with open(self.log_file, "w") as f:
            json.dump(self.history, f, indent=2)

    def _append_md(self, entry):
        with open(self.md_file, "a") as f:
            timestamp = entry["timestamp"].split("T")[1].split(".")[0]
            etype = entry["type"].upper()
            content = entry["content"]
            
            f.write(f"### [{timestamp}] {etype}\n")
            if etype == "THOUGHT":
                f.write(f"> {content}\n\n")
            elif etype == "ACTION":
                tool = content.get("tool")
                args = content.get("args")
                f.write(f"**Tool:** `{tool}`\n**Args:** `{args}`\n\n")
            elif etype == "OUTPUT":
                # Truncate if too long for MD readability
                if len(str(content)) > 1000:
                    display_content = str(content)[:1000] + "... [TRUNCATED]"
                else:
                    display_content = content
                f.write(f"```\n{display_content}\n```\n\n")
            else:
                f.write(f"{content}\n\n")

class OutputParser:
    """Helper to parse raw tool output for small context windows."""
    
    @staticmethod
    def parse_nmap(output: str) -> str:
        """Extract open ports and services from Nmap output."""
        lines = output.split('\n')
        parsed = []
        capture = False
        for line in lines:
            if "PORT" in line and "STATE" in line and "SERVICE" in line:
                capture = True
                parsed.append(line)
                continue
            if capture and "/tcp" in line and "open" in line:
                parsed.append(line)
        
        if not parsed:
            return "No open ports found or parsing failed. Raw start: " + output[:200]
        return "\n".join(parsed)
