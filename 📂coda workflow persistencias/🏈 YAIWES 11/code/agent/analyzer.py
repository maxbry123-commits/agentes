import os
import yaml
import json
from typing import Dict
from agent.memory import Memory
from utils.llm_request import LLMRequest
from jinja2 import Environment, FileSystemLoader
from utils.text import fix_json_with_llm
from config import get_project_root


class Analyzer:
    def __init__(self, config: dict, problem: str, mode: str = "ctf"):
        self.config: dict = config
        prompt_version = config.get("prompt_version", "v1")
        self.env = Environment(loader=FileSystemLoader(
            os.path.join(get_project_root(), "prompts", prompt_version)
        ))
        self.analyze_llm = LLMRequest("analyzer")
        self.problem = problem
        self.mode = mode
        # 根据模式加载不同的 Prompt 文件
        prompt_file = "pentest_prompt.yaml" if mode == "pentest" else "prompt.yaml"
        prompt_path = os.path.join(get_project_root(), "prompts", prompt_version, prompt_file)
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt: dict = yaml.safe_load(f)

    def analyze_step_output(
        self, memory: Memory, solution_plan: str, output: str, step_num: int
    ) -> Dict:
        """使用LLM分析步骤输出。"""
        history_summary = memory.get_summary()

        # 渗透模式：附加已确认发现
        findings_context = ""
        if self.mode == "pentest":
            findings_context = memory.get_summary(include_key_facts=True)[:1000]

        # 对发给分析 LLM 的输出做可配置截断（与 llm_summary_threshold 对齐）
        _max_output = self.config.get("llm_summary_threshold", 16384)
        template = self.env.from_string(self.prompt.get("step_analysis", ""))
        prompt = template.render(
            question=self.problem,
            scope=self.problem,
            content=solution_plan,
            output=output[:_max_output],
            solution_plan=solution_plan,
            step_num=step_num,
            history_summary=history_summary,
            findings=findings_context,
        )

        response = self.analyze_llm.text_completion(prompt, json_check=True)

        try:
            result = json.loads(response.choices[0].message.content)
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, KeyError) as e:
            try:
                content = fix_json_with_llm(response.choices[0].message.content, e)
                result = json.loads(content)
                if isinstance(result, dict):
                    return result
            except (ValueError, json.JSONDecodeError):
                pass

        return self._fallback_analysis()

    def _fallback_analysis(self) -> Dict:
        """LLM 输出无法解析时的回退分析（v2: progress_level 替代 no_progress/new_info）。"""
        if self.mode == "pentest":
            return {
                "vulnerability_found": False,
                "vulnerability": None,
                "attack_surface_covered": [],
                "should_continue": True,
                "next_priority": None,
                "terminate_all": False,
                "progress_level": "minor",
                "analysis": "LLM输出解析失败，无法自动分析",
            }
        return {
            "flag_found": False,
            "analysis": "LLM输出解析失败，无法自动分析",
            "terminate": False,
            "progress_level": "minor",
        }
