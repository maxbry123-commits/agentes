import copy
import os
import re
import sys
import json
import time
import asyncio
import tempfile
import traceback
import subprocess
from pathlib import Path
from abc import abstractmethod
from dataclasses import dataclass
from pydantic import BaseModel, Field
from typing import AsyncGenerator, Union, Dict, Tuple, List, Callable

from model import LLM
from monitor import Monitor, SubTask
from log import AgentLogger, LogLevel
from memory_manager import MemoryManager
from tool import generate_tool_schema, ToolRegistry, generate_tool_des
from utils import extract_json_codeblock, create_message, deep_update, pretty_print_trajectory, safe_json_parse
from prompt.system_prompt import MUSE_list_fact_prompt, MUSE_plan_subtasks_prompt, \
    MUSE_execute_subtask_prompt, MUSE_action_with_observation__instruction_prompt, task_final_plan_prompt, \
    task_replan_for_success_prompt, task_replan_for_failure_prompt, MUSE_execute_subtask_access_guide_prompt
from prompt.reflect_prompt import reflect_check_completion_prompt, reflect_update_application_memory_prompt, \
    reflect_analyse_failure__display_prompt, reflect_sys_prompt, reflect_plan__display_prompt, reflect_analyse_success__display_prompt, \
    reflect_analyse_failure__instruction_prompt, reflect_execute_check__instruction_prompt, reflect_action_with_observation_prompt, reflect_plan__instruction_prompt
from prompt.summarize_prompt import reflect_tool_enhance_prompt, reflect_methodology_enhance_prompt, \
    summarize_success_and_failure_prompt, merge_methodology_prompt, merge_application_prompt


@dataclass
class ToolCallParseResult:
    exist_tool_call: bool
    tool_json: Union[Dict[str, str], None]
    parse_msg: str

class ToolResultFormatValidator(BaseModel):
    data: str = Field(..., description="Tool execution results")
    instruction: str = Field(..., description="Instruction for LLMs bundled with the tool")

class BaseAgent:
    def __init__(
            self,
            init_model_name: str,
            sys_prompt_template: str,
            output_dir: str="outputs",
            agent_name: str="default_agent",
            task_name: str="default_task"
    ):
        self.subtask_action_limit = None
        self.num_time_limit = None
        self.num_subtasks_limit = None
        self.num_actions_limit = None
        self.logger = AgentLogger(level=LogLevel.INFO)
        self.agent_name: str = agent_name
        self.task_name: str = task_name
        self.output_dir: Path = Path(output_dir)
        self.llm = LLM(init_model_name)
        self.monitor = Monitor()

        self.tool_registrar = ToolRegistry()
        self.tool_registrar.load_tools(tools_folder="toolbox")

        self.history = []
        self.sys_prompt_template = sys_prompt_template

    def render_tool_schema_texts(self) -> str:
        tool_schemas = []
        for tool_name, tool_func in self.tool_registrar.tools.items():
            self.monitor.init_tool(tool_name)
            tool_schemas.append(generate_tool_schema(tool_func))

        tools_schema_texts = "\n".join(tool_schemas)
        return tools_schema_texts

    def _get_output_dir(self) -> Path:
        return self.output_dir / self.agent_name / self.task_name

    def save_history(self, trajectory: List[dict]):
        try:
            output_path = self._get_output_dir() / "history.txt"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            history = pretty_print_trajectory(trajectory, show_full_content=True, print_to_terminal=False)
            with output_path.open("w", encoding="utf-8") as f:
                f.write(history)
            print(f"✅ History saved to: {output_path}")
        except Exception as e:
            import traceback
            print(f"❌ Failed to save history: {e}")
            traceback.print_exc()

    @staticmethod
    def python_interpreter(code: str, work_dir: str = "/workspace") -> str:
        STATUS_EXECUTED = "CODE_EXECUTED"
        STATUS_FAILURE_TIMEOUT = "TOOL_FAILURE_TIMEOUT"
        STATUS_FAILURE_EXCEPTION = "TOOL_FAILURE_UNKNOWN_EXCEPTION"

        timeout = 270
        result = {}
        script_path = None

        try:
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False, dir=work_dir, encoding='utf-8') as f:
                f.write(code)
                script_path = f.name

            proc = subprocess.run(
                [sys.executable, script_path],
                capture_output=True, text=True, timeout=timeout, cwd=work_dir, encoding='utf-8', errors='replace'
            )

            result = {
                "execution_status": STATUS_EXECUTED,
                "code_result": {
                    "returncode": proc.returncode
                },
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip()
            }

        except subprocess.TimeoutExpired:
            result = {
                "execution_status": STATUS_FAILURE_TIMEOUT,
                "stderr": f"Code execution timed out (terminated after {timeout} seconds)."
            }

        except Exception:
            result = {
                "execution_status": STATUS_FAILURE_EXCEPTION,
                "exception": traceback.format_exc()
            }

        finally:
            if script_path and os.path.exists(script_path):
                try:
                    os.unlink(script_path)
                except Exception:
                    pass

        return json.dumps(result, ensure_ascii=False, indent=2)

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict
    ) -> AsyncGenerator[Tuple[str, str], None]:
        tool_result = ""
        if tool_name == "python":
            result = self.python_interpreter(arguments["code"])
            yield "[STREAMING]", result
            tool_result = result
        else:
            tool_function = self.tool_registrar.get_tool(tool_name)
            if tool_function:
                try:
                    async for tool_chunk in tool_function(**arguments):
                        ToolResultFormatValidator.model_validate(tool_chunk)

                        chunk = tool_chunk["data"]
                        yield "[STREAMING]", chunk

                        tool_result += chunk
                    self.monitor.inc_tool_call(tool_name)
                except Exception as e:
                    tool_result = f"An error occurred while executing the tool, {e}\nTool name: {tool_name}"
                    self.monitor.inc_tool_error(tool_name)
            else:
                tool_result = f"An error occurred while executing the tool. The tool {tool_name} was not found."

        yield "[DONE]", f"<tool_response>\n{tool_result}\n</tool_response>"

    @staticmethod
    def parse_tool_call(ai_response: str) -> 'ToolCallParseResult':
        tool_call_match = re.search(r'<tool_call>\s*({.*?})\s*</tool_call>', ai_response, re.DOTALL)
        if tool_call_match:
            tool_call_text = tool_call_match.group(1).strip()
            tool_call_json, parse_err = safe_json_parse(tool_call_text)
            if tool_call_json is None:
                return ToolCallParseResult(True, None, f"❌ Failed to parse JSON tool_call block.\n↳ Error: {parse_err}")

            tool_name = tool_call_json.get('name')
            arguments = tool_call_json.get('arguments')
            if tool_name is None:
                return ToolCallParseResult(True, None, "Tool call JSON does not contain key: 'name'")
            if arguments is None:
                return ToolCallParseResult(True, None, "Tool call JSON does not contain key: 'arguments'")

            return ToolCallParseResult(
                True,
                {"tool_name": tool_name, "arguments": arguments},
                "✅ Successfully extracted tool call JSON."
            )

        code_match = re.search(r'<code>\s*(.*?)\s*</code>', ai_response, re.DOTALL)
        if code_match:
            python_code = code_match.group(1).strip()

            try:
                return ToolCallParseResult(
                    True,
                    {"tool_name": "python", "arguments": {"code": python_code}},
                    "✅ Successfully extracted python code."
                )
            except Exception as e:
                return ToolCallParseResult(True, None, "❌ Exception occurred while extracting python code.")

        return ToolCallParseResult(False, None, "No tool_call or python code found in the output.")

    async def _in_context_step(self, prompt: str):
        """
        Have a single-step conversation with LLM. Both the input prompt and LLM's reply will be saved in the Agent's history.
        """
        ai_response = ""
        async for chunk in self.llm.async_stream_generate(prompt, history=self.history):
            ai_response += chunk
            yield chunk
        self.history.extend([
            create_message("user", prompt),
            create_message("assistant", ai_response)
        ])

    @abstractmethod
    async def _run(self, prompt: str) -> AsyncGenerator[str, None]:
        if False:
            yield ""

    async def single_turn_chat(self, prompt: str, llm_name: str = None) -> None:
        if llm_name is not None:
            self.llm = LLM(llm_name)
        async for chunk in self._in_context_step(prompt):
            print(chunk)

    async def run(self, prompt: str, llm_name: str=None, subtask_action_limit: int=None, num_actions_scale: float=None, subtasks_limit: int=None, time_limit: int=None, verbose: bool=True) -> None:
        if llm_name is not None:
            self.llm = LLM(llm_name)

        if subtask_action_limit is not None:
            self.subtask_action_limit = subtask_action_limit
            if num_actions_scale is not None:
                self.num_actions_limit = subtask_action_limit * num_actions_scale
        if subtasks_limit is not None:
            self.num_subtasks_limit = subtasks_limit
        if time_limit is not None:
            self.num_time_limit = time_limit

        async for chunk in self._run(prompt):
            if verbose:
                print(chunk, end="", flush=True)
            else:
                if len(chunk) > 1000:
                    display = chunk[:200] + "\n...The content is too long and has been omitted...\n" + chunk[-200:]
                else:
                    display = chunk
                print(display, end="", flush=True)


class MUSE(BaseAgent):
    def __init__(
            self,
            init_model_name: str,
            sys_prompt_template: str,
            memory_dir: str,
            agent_name: str="MUSE_default",
            task_name: str="new_task",
            output_dir: str="outputs",
            mode_label: str= "train",
            task_round: int=1,
            use_memory: bool = True,
            update_memory: bool = True,
            env_feedback_func: Callable[..., str]=None,
            env_feedback_args: dict=None,
            lang="en"
    ):
        super().__init__(init_model_name, sys_prompt_template, output_dir, agent_name, task_name)
        self.mode = mode_label
        self.task_round = task_round

        self.use_memory: bool = use_memory
        self.update_memory: bool = update_memory

        tool_schema_texts = self.render_tool_schema_texts()
        self.memory_manager = MemoryManager(memory_dir, self.logger, self._get_output_dir(), sys_prompt_template, tool_schema_texts, use_memory)
        self.history = self.memory_manager.get_history()

        if (env_feedback_func is None) != (env_feedback_args is None):
            raise ValueError("env_feedback_func and env_feedback_args must both be None, or both be not None.")
        self.env_feedback_func: Callable[[str], str] = env_feedback_func
        self.env_feedback_args = env_feedback_args

        self.language_prompt = "\n请以中文输出" if lang=="zh" else ""

        self.to_do_subtasks: List[SubTask] = []

    async def _run(self, task: str) -> AsyncGenerator[str, None]:
        # All yield results are only used to display results to the user.
        # The context analysis is based on the data stored in the agent.history property.

        st_time = time.time()
        # plan
        plan_trajectory = []
        async for chunk in self.initial_plan(task, plan_trajectory):
            yield chunk
        self.logger.log_task(self.history[-1]["content"][0]["text"], "PLANNING···", "Multi-step Subtasks Plan")
        # The plan trajectory includes three messages:
        #   system message,
        #   user message-> content is the `task`,
        #   assistant message-> content is the result of the entire planning step, including the `task execution plan`

        # pretty_print_trajectory(plan_trajectory, show_full_content=True, print_to_terminal=True)

        # execute
        while self.to_do_subtasks:
            cur_subtask = self.to_do_subtasks.pop(0)
            cur_subtask.set_index(self.monitor.subtasks_used + 1)
            cur_subtask_prompt = f"SubTask{cur_subtask.index}: {cur_subtask.name}\nGoal: {cur_subtask.goal}"
            self.logger.log_task(cur_subtask_prompt, subtitle=f"EXECUTING···", title=f"Execute Subtask")

            subtask_retry_time_limit = 2
            temperature = 0.5
            need_guide = True
            # react block
            while cur_subtask.try_times < subtask_retry_time_limit:
                cur_subtask.try_times += 1
                async for chunk in self.exec_subtask(cur_subtask_prompt, self.subtask_action_limit, cur_subtask.trajectory, subtask_name=cur_subtask.name, temperature=temperature, need_guide=need_guide):
                    yield chunk
                # Used to block reflection =====================
                # cur_subtask.finish = True
                # break
                # ===================================

                async for chunk in self.reflect(task, cur_subtask):
                    yield chunk

                if cur_subtask.finish:
                    break
                if cur_subtask.try_times < subtask_retry_time_limit:
                    cur_subtask_prompt += "\nThe goal of this subtask has not been achieved yet, please continue"
                    temperature = 1.5
                    need_guide = False
                    self.logger.log_task(cur_subtask_prompt, subtitle="EXECUTING···", title=f"Re-execute Subtask {cur_subtask.index}: {cur_subtask.name}")
                else:
                    self.logger.log_task(f"SubTask{cur_subtask.index}: {cur_subtask.name} Failed After {cur_subtask.try_times} Retries.", subtitle="EXECUTION DONE", title=f"Subtask Failed")

            # record done sub-task
            self.monitor.add_done_subtask(cur_subtask)
            # add trajectory into main history
            add_trajectory = copy.deepcopy(cur_subtask.trajectory)
            self.memory_manager.trim_traj(add_trajectory)
            self.memory_manager.add_traj(add_trajectory)

            if self.is_limit_exceeded(action_used=self.monitor.num_actions, subtasks_used=self.monitor.subtasks_used, time_used=time.time() - st_time):
                break

            if not cur_subtask.finish:
                async for chunk in self.replan(task_replan_for_failure_prompt.format(try_times=cur_subtask.try_times), task):
                    yield chunk
            elif len(self.to_do_subtasks) > 0:
                async for chunk in self.replan(task_replan_for_success_prompt, task):
                    yield chunk
            else:
                async for chunk in self.replan(task_final_plan_prompt, task):
                    yield chunk
            self.logger.log_task(self.history[-1]["content"][0]["text"], "RE-PLANNING···",
                                 "Multi-Step Subtasks Re-Plan")

            # self.memory_manager.rm_traj_by_length(len(add_trajectory) - 1, 5)
            # self.history[-1]["content"][0]["text"] = "[SYSTEM INFO: History subtask tracks removed for brevity]\n" + self.history[-5]["content"][0]["text"]

        if not self.to_do_subtasks and self.monitor.done_subtasks[-1].finish:
            self.logger.log_task(f"Agent finish all the subtasks.\nTotal action steps: {self.monitor.num_actions}.", subtitle="DONE", title="Task Finished")
        else:
            self.logger.log_task(f"Agent don't finish all the subtasks.\nTotal action steps: {self.monitor.num_actions}.", subtitle="DONE", title="Task Failed")

        self.monitor.update_time(round(time.time() - st_time, 2))
        self.logger.log_task(f"Time consumed to run the task: {self.monitor.time_used}s.", "END", "End Agent")

        # reflection
        async for chunk in self.summarize_and_enhance():
            yield chunk

        self.memory_manager.save_run_artifacts(self.monitor)
        return

    async def initial_plan(self, task: str, plan_trajectory: List[dict]):
        user_prompt = f"<task>\n{task}\n</task>"
        async for chunk in self._multi_step_plan(user_prompt):
            yield chunk
        plan_trajectory.extend(self.history[:])

    async def exec_subtask(
            self,
            prompt: str,
            action_limit: int = None,
            subtask_trajectory: List[dict] = None,
            subtask_name: str = "",
            temperature: float = 1.0,
            need_guide: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Determine if the LLM output contains tool execution requirements.
        If so, execute the tool. This process repeats until the LLM output no longer contains tool execution requirements.
        """
        working_trajectory = copy.deepcopy(subtask_trajectory)
        def _append_turn(user_text: str, ai_text: str):
            subtask_trajectory.extend([
                create_message("user", user_text),
                create_message("assistant", ai_text)
            ])
            working_trajectory.extend([
                create_message("user", user_text),
                create_message("assistant", ai_text)
            ])

        start_index = len(subtask_trajectory)
        if need_guide:
            cur_prompt = MUSE_execute_subtask_prompt.format(subtask=prompt) + MUSE_execute_subtask_access_guide_prompt + self.language_prompt
        else:
            cur_prompt = MUSE_execute_subtask_prompt.format(subtask=prompt) + self.language_prompt
        exist_tool_call = True
        actions = 0
        while exist_tool_call and (action_limit is None or actions < action_limit):
            self.memory_manager.update_system_prompt()
            self.memory_manager.trim_traj(working_trajectory, preserve_last=3)

            ai_response = ""
            async for chunk in self.llm.async_stream_generate(
                    cur_prompt if actions == 0 else MUSE_action_with_observation__instruction_prompt.format(observation=cur_prompt) + self.language_prompt,
                    history=self.history + working_trajectory, temperature=temperature
            ):
                yield chunk
                ai_response += chunk

            if not ai_response.strip():
                yield "[SYSTEM WARNING: LLM response is empty, the ReAct workflow will end.]"

            _append_turn(cur_prompt, ai_response)

            parse_result = self.parse_tool_call(ai_response)
            if parse_result.tool_json:
                self.logger.log_task(str(parse_result.tool_json), subtitle="SUB-TASK REACTING······", title=f"ReAct: Action {actions + 1} | For: {subtask_name}")

                tool_call_result = None
                async for status, chunk in self.call_tool(**parse_result.tool_json):
                    if status == "[DONE]":
                        yield "\n* * * * * * * * * * * *\n"
                        tool_call_result = chunk
                    else:
                        yield chunk

                assert tool_call_result is not None, "The tool call did not return the final result correctly. Please check the tool logic."
                cur_prompt = f"Observation: \n{tool_call_result}\n"
            else:
                if parse_result.exist_tool_call:
                    self.logger.log_task(content="❌ JSON parsing failed\n"
                                                 f"↳ Error message: {parse_result.parse_msg}\n",
                        subtitle="SUB-TASK REACTING······",
                        title=f"ReAct: Try Action {actions + 1} Failed | For: {subtask_name}"
                    )
                    cur_prompt = (f"Observation: \n{parse_result.parse_msg}\nAn error occurred when the parsing tool called JSON. Please consider the following: "
                                  "1. Was the correct JSON format text output? "
                                  "2. Was the correct tool selected and the correct parameters entered? "
                                  "3. One point worth noting is whether the string parameters were not enclosed in quotes.")
                else:
                    cur_prompt = parse_result.parse_msg

            exist_tool_call = parse_result.exist_tool_call
            actions += 1

        if actions == action_limit:
            self.monitor.inc_subtask_limit_exceeded()
            reach_limit_warning = f"\n\n[SYSTEM WARNING: React action limit has been reached. Maximum allowed: {action_limit}.]"
            yield reach_limit_warning
            _append_turn(cur_prompt, reach_limit_warning)
        subtask_trajectory[start_index] = create_message("user", prompt)

        self.logger.log_task(f"Current subtask ReAct execution actions: {actions}", subtitle="SUB-TASK REACT DONE", title=f"ReAct: No More Action | For: {subtask_name}")
        self.monitor.add_actions(actions)
        self.logger.log_task(f"The total number of actions currently executed is: {self.monitor.num_actions}.", "COUNTING···", "Num Actions")
        return

    async def reflect(self, task, cur_subtask: SubTask):
        env_feedback = self.get_env_feedback(cur_subtask.trajectory)

        st_time = time.time()
        reflect_history = [create_message("system", reflect_sys_prompt.format(tools=self.memory_manager.tool_schema_texts))]

        plan_prompt = reflect_plan__display_prompt.format(
            task=task,
            done_subtasks=str(self.monitor.get_done_subtask_for_reflection()),
            trajectory=pretty_print_trajectory(cur_subtask.trajectory, True, False)
        )
        check_list_str = ""
        async for chunk in self.llm.async_stream_generate(plan_prompt + reflect_plan__instruction_prompt + self.language_prompt, history=reflect_history):
            yield chunk
            check_list_str += chunk

        check_list = extract_json_codeblock(check_list_str)[0].items()
        check_steps = "\n    ".join([f"{i + 1}. {check_step}" for i, (check_step, check_goal) in enumerate(check_list)])
        reflect_history.extend([
            create_message("user", plan_prompt),
            create_message("assistant", f"* The check plan can be divided into the following steps:\n    {check_steps}")
        ])

        for check_step, check_goal in check_list:
            check_prompt = f"CheckStep:{check_step}\nCheckGoal:{check_goal}"
            self.logger.log_task(check_prompt, subtitle="SUB-TASK REFLECT CHECKING···", title=f"Check: {check_step}")
            async for chunk in self._reflect_react(check_prompt, reflect_history):
                yield chunk


        finish_str = await self.llm.async_generate(env_feedback + reflect_check_completion_prompt, history=reflect_history)

        finish = extract_json_codeblock(finish_str)[0]
        cur_subtask.finish = True if finish.get("finish", "no") == "yes" else False

        yield "\n\n"

        check_report = ""
        async for chunk in self.llm.async_stream_generate(
                "Please compile your inspection results into a short report and submit it to the Task Agent. The report should at least include three parts: 'Title', 'Checklist Details', and 'Conclusion'." + self.language_prompt,
                history=reflect_history
        ):
            yield chunk
            check_report += chunk
        cur_subtask.reflection.check_report = check_report
        self.logger.log_task(check_report, subtitle="SUB-TASK REFLECT DONE", title="Check Report")

        yield "\n\n"

        # analyze by task agent
        analysis = ""
        if not cur_subtask.finish:
            analysis__display_prompt = reflect_analyse_failure__display_prompt.format(check_report=check_report)
            async for chunk in self.llm.async_stream_generate(analysis__display_prompt + reflect_analyse_failure__instruction_prompt + self.language_prompt, history=self.history):
                yield chunk
                analysis += chunk
            cur_subtask.trajectory.extend([
                create_message("user", analysis__display_prompt),
                create_message("assistant", analysis)
            ])
        else:
            if self.update_memory:
                async for chunk in self.llm.async_stream_generate(
                        env_feedback + reflect_update_application_memory_prompt.format(guidance=self.memory_manager.application_enhance_dict) + self.language_prompt,
                        history=reflect_history
                    ):
                    yield chunk
                    analysis += chunk
                app_memo_dict = extract_json_codeblock(analysis)[0]
                if app_memo_dict:
                    self.memory_manager.update_and_save_app_memory(app_memo_dict)
                else:
                    self.monitor.add_memory_update_exception("update_procedural_memory", analysis)
            cur_subtask.trajectory.extend([
                create_message("user", reflect_analyse_success__display_prompt.format(check_report=check_report)),
                create_message("assistant", "Got it! I'll continue with the task.")
            ])
        cur_subtask.reflection.analysis = analysis
        cur_subtask.reflection.time_used = round(time.time()  - st_time, 2)
        cur_subtask.reflect_trajectory = reflect_history

    async def replan(self, prompt, task: str):
        user_prompt = prompt + f"\nAlways remember that your ultimate goal is to complete task:\n<task>\n{task}\n</task>"
        async for chunk in self._multi_step_plan(user_prompt):
            yield chunk

    async def summarize_and_enhance(self):
        if self.update_memory:
            summarize_prompt = "Please summarize what you have done for this task." + self.language_prompt
            async for chunk in self._in_context_step(summarize_prompt):
                yield chunk

            env_feedback = self.get_env_feedback([])

            async for chunk in self._in_context_step(summarize_success_and_failure_prompt.format(env_feedback=env_feedback) + self.language_prompt):
                yield chunk

            # Gather full tool memory include tool_description and tool_instruction
            tool_memory_dict = {}
            for tool_name, tool_func in self.tool_registrar.tools.items():
                tool_memory_dict[tool_name] = {
                    "tool_description": generate_tool_des(tool_func),
                    "tool_instruction": ""
                }
            deep_update(tool_memory_dict, self.memory_manager.tool_enhance_dict)

            inc_tasks = [self.llm.async_generate(prompt + self.language_prompt, history=self.history, max_tokens=None) for prompt in [
                reflect_tool_enhance_prompt.format(tools=tool_memory_dict),
                reflect_methodology_enhance_prompt
            ]]
            responses = await asyncio.gather(*inc_tasks)
            enhance_dicts = []
            for resp in responses:
                yield "\n\n" + resp
                enhance_dicts.append(extract_json_codeblock(resp)[0])
            tool_enhance_dict, methodology_enhance_dict = enhance_dicts
            for tool_name in tool_enhance_dict:
                self.monitor.inc_tool_modified(tool_name)

            merge_tasks = [self.llm.async_generate(prompt + self.language_prompt, max_tokens=None) for prompt in [
                merge_application_prompt.format(guidance=self.memory_manager.application_enhance_dict),
                merge_methodology_prompt.format(
                    old_methodology=str(self.memory_manager.methodology_enhance_dict),
                    new_methodology=str(methodology_enhance_dict)
                )
            ]]
            responses = await asyncio.gather(*merge_tasks)
            merge_dicts = []
            for resp in responses:
                yield "\n\n" + resp
                merge_dicts.append(extract_json_codeblock(resp)[0])
            application_enhance_dict, methodology_enhance_dict = merge_dicts

            # Update three type of memory
            deep_update(self.memory_manager.tool_enhance_dict, tool_enhance_dict)
            if application_enhance_dict:
                self.memory_manager.application_enhance_dict = application_enhance_dict
            else:
                self.monitor.add_memory_update_exception("summarise_procedural_memory", str(application_enhance_dict))
            if methodology_enhance_dict:
                self.memory_manager.methodology_enhance_dict = methodology_enhance_dict
            else:
                self.monitor.add_memory_update_exception("summarise_strategic_memory", str(methodology_enhance_dict))
            # Save
            self.memory_manager.save_all_memory_to_disk()
        else:
            self.logger.log_task("Pass the summarize_and_enhance step", subtitle="WARNING···", title="update_memory set to False")

    async def _multi_step_plan(self, user_prompt: str):
        """
        Multistep task planning, but the instructions during planning are not saved to working memory.
        Ultimately, only two messages are added to working memory: user_message->user_prompt, assistant_message->task_plan
        """
        self.llm = LLM("gemini-2.5-flash-thinking")

        cur_prompt = user_prompt + "\n\n" + MUSE_list_fact_prompt + self.language_prompt
        known_facts = ""
        async for chunk in self.llm.async_stream_generate(cur_prompt, history=self.history):
            yield chunk
            known_facts += chunk
        self.memory_manager.add_turn(create_message("user", user_prompt), create_message("assistant", known_facts))
        yield "\n\n"

        # unknown_facts = ""
        # async for chunk in self.llm.async_stream_generate(MUSE_confirm_fact_prompt, history=self.history):
        #     yield chunk
        #     unknown_facts += chunk
        # self.history[-1] = create_message("assistant", f"{known_facts}\n\n{unknown_facts}")
        # yield "\n\n"

        plan_data = {}
        cur_prompt = MUSE_plan_subtasks_prompt + self.language_prompt
        for attempt in range(3):
            multi_steps_plan = ""
            async for chunk in self.llm.async_stream_generate(
                cur_prompt,
                history=self.history
            ):
                yield chunk
                multi_steps_plan += chunk

            plan_data, err = extract_json_codeblock(multi_steps_plan)

            if err is None:
                break
            else:
                self.monitor.add_memory_update_exception("plan", err)
                print(f"⚠️ Parse failed on attempt {attempt + 1}: {err}")
                cur_prompt += (f"\nLast time your generation is {multi_steps_plan}\n"
                               f"Retry and avoid such error: {err}")
        else:
            print("❌ All retries failed")

        self.to_do_subtasks = [SubTask(name=k, goal=v) for k, v in plan_data.items()]
        # All planning results are saved into an assistant message, and the history records in the planning steps are deleted.
        subtasks = "\n    ".join([f"{i + 1}. {subtask.name}: {subtask.goal}" for i, subtask in enumerate(self.to_do_subtasks)])
        self.history[-1] = create_message("assistant",f"{known_facts}\n\n* The task can be divided into the following subtasks:\n    {subtasks}")

        self.llm = LLM("gemini-2.5-flash")

    async def _reflect_react(self, prompt: str, trajectory: List[dict], action_limit: int = 8):
        start_index = len(trajectory)
        cur_prompt = reflect_execute_check__instruction_prompt.format(check_step=prompt, step_limit=action_limit) + self.language_prompt
        exist_tool_call = True
        actions = 0
        while exist_tool_call and actions < action_limit:
            ai_response = ""
            async for chunk in self.llm.async_stream_generate(
                    cur_prompt if actions == 0 else reflect_action_with_observation_prompt.format(observation=cur_prompt) + self.language_prompt,
                    history=trajectory
            ):
                yield chunk
                ai_response += chunk

            if not ai_response.strip():
                yield "[SYSTEM WARNING: LLM response is empty, the ReAct workflow will end.]"

            trajectory.extend([
                create_message("user", cur_prompt),
                create_message("assistant", ai_response)
            ])

            parse_result = self.parse_tool_call(ai_response)

            if parse_result.tool_json:
                self.logger.log_task(str(parse_result.tool_json), subtitle="SUB-TASK REFLECT REACTING······", title=f"ReAct Check: Action {actions + 1}, Max {action_limit}")

                tool_call_result = None
                async for status, chunk in self.call_tool(**parse_result.tool_json):
                    if status == "[DONE]":
                        yield "\n* * * * * * * * * * * *\n"
                        tool_call_result = chunk
                    else:
                        yield chunk

                assert tool_call_result is not None, "The tool call did not return the final result correctly. Please check the tool logic."

                cur_prompt = f"Observation: \n{tool_call_result}"
            else:
                if parse_result.exist_tool_call:
                    self.logger.log_task(content="❌ JSON parsing failed\n"
                                                 f"↳ Error message: {parse_result.parse_msg}\n",
                        subtitle="REFLECTING······",
                        title=f"Check: Try Action {actions + 1} Failed"
                    )
                    cur_prompt = (f"Observation: \n{parse_result.parse_msg}\nAn error occurred when the parsing tool called JSON. Please consider the following: "
                                  "1. Was the correct JSON format text output? "
                                  "2. Was the correct tool selected and the correct parameters entered? "
                                  "3. One point worth noting is whether the string parameters were not enclosed in quotes.")
                else:
                    cur_prompt = parse_result.parse_msg

            exist_tool_call = parse_result.exist_tool_call
            actions += 1

        if actions == action_limit:
            reach_limit_warning = f"\n\n[SYSTEM WARNING: React action limit has been reached. Maximum allowed: {action_limit}.]"
            yield reach_limit_warning
            trajectory.extend([
                create_message("user", cur_prompt),
                create_message("assistant", reach_limit_warning)
            ])
        trajectory[start_index] = create_message("user", prompt)

    def get_env_feedback(self, subtask_trajectory) -> str:
        # The agent trajectory is stored here for environmental scoring
        self.save_history(self.history + subtask_trajectory)
        if self.env_feedback_func is not None:
            result = f"<env_feedback>\n{self.env_feedback_func(**self.env_feedback_args)}\n</env_feedback>"
            self.logger.log_task(result, subtitle="EVALUATING···", title="Get Env Feedback")
            return (f"{result}\n"
                    "The above are the current scoring points and score status of this task, which you can combine for subsequent analysis.\n")
        else:
            return ""

    async def call_tool(self, tool_name: str, arguments: dict) -> AsyncGenerator[tuple, None]:
        tool_result = {
            "data": "",
            "instruction": ""
        }
        if tool_name == "python":
            result = self.python_interpreter(arguments["code"])
            yield "[STREAMING]", result
            tool_result["data"] = result
        else:
            tool_function = self.tool_registrar.get_tool(tool_name)
            if tool_function:
                try:
                    async for tool_chunk in tool_function(**arguments):
                        ToolResultFormatValidator.model_validate(tool_chunk)

                        chunk = tool_chunk["data"]
                        yield "[STREAMING]", chunk

                        tool_result["data"] += chunk
                        tool_result["instruction"] = tool_chunk.get("instruction", "")
                    if self.use_memory and tool_name in self.memory_manager.tool_enhance_dict:
                        tool_result["instruction"] = self.memory_manager.tool_enhance_dict[tool_name]["tool_instruction"]
                    self.monitor.inc_tool_call(tool_name)
                except Exception as e:
                    tool_result["data"] = f"An error occurred while executing the tool, tool name: {tool_name}, {e}:\n{traceback.format_exc()}"
                    tool_result["instruction"] = "Default instructions for specific errors: Please analyze the error message, try again, or use other tools"
                    self.monitor.inc_tool_error(tool_name)
            else:
                tool_result["data"] = f"An error occurred while executing the tool. The tool {tool_name} was not found."
                tool_result["instruction"] = "Specific error default instruction: Please try using another tool"

        yield "[DONE]", str(
            f"<tool_response>\n{tool_result.get('data')}\n</tool_response>\n"
            f"<tool_instruction>\n{tool_result.get('instruction')}\n</tool_instruction>"
        )

    def is_limit_exceeded(self, action_used: int, subtasks_used: int, time_used: float) -> bool:
        log_args = {"content": f"Done at subtask {subtasks_used}, over the {{limit}}", "subtitle": "DONE", "title": "Limit Exceeded"}
        if self.num_actions_limit is not None and action_used >= self.num_actions_limit:
            log_args["content"] = log_args["content"].format(limit=f"actions limit {self.num_actions_limit}.")
            self.logger.log_task(**log_args)
            return True
        if self.num_subtasks_limit is not None and subtasks_used >= self.num_subtasks_limit:
            log_args["content"] = log_args["content"].format(limit=f"subtasks limit {self.num_subtasks_limit}.")
            self.logger.log_task(**log_args)
            return True
        if self.num_time_limit is not None and time_used >= self.num_time_limit:
            log_args["content"] = log_args["content"].format(limit=f"time limit {self.num_time_limit}.")
            self.logger.log_task(**log_args)
            return True
        return False

    def _get_output_dir(self) -> Path:
        output_dir =  self.output_dir / self.agent_name / self.mode / self.task_name / f"round_{self.task_round}"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def render_tool_schema_texts(self) -> str:
        tool_schemas = []
        tool_enhance_dict = self.memory_manager.tool_enhance_dict if hasattr(self, 'memory_manager') else self._load_memory_for_render()

        for tool_name, tool_func in self.tool_registrar.tools.items():
            self.monitor.init_tool(tool_name)
            if self.use_memory and tool_name in tool_enhance_dict:
                tool_schemas.append(
                    generate_tool_schema(tool_func, tool_enhance_dict[tool_name].get("tool_description", "")))
            else:
                tool_schemas.append(generate_tool_schema(tool_func))

        tools_schema_texts = "\n".join(tool_schemas)
        self.logger.log_task(tools_schema_texts, subtitle="LOADING······", title="Load Tools")
        return tools_schema_texts

    @staticmethod
    def _load_memory_for_render() -> dict:
        # A helper to load memory just for render_tool_schema_texts, used **before** memory_manager is initialized
        memory_dir = Path("memory") # Default path, adjust if necessary
        tool_enhance_path = memory_dir / "tool_memory.json"
        try:
            with open(tool_enhance_path, "r", encoding="utf-8") as f:
                text = f.read()
                if not text.strip():
                    return {}
                return json.loads(text)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
