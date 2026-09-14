from smolagents import CodeAgent
from smolagents.tools import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
import subprocess
import os
from pprint import pprint
import json
import logging
from subprocess import CalledProcessError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ExperimentAgent(CodeAgent):
    def __init__(self, 
                 model, 
                 root_dir: str,
                 prompt_templates: dict,
                 tools: list[Tool] = [],
                 env_name: str = None,
                 **kwargs):
        self.root_dir = root_dir
        self.run_logs = []
        self.token_usage = {
            "input": 0,
            "output": 0
        }
        self.env_name = env_name
        file_management_tools = generate_file_management_tools(root_dir)
        new_tools = tools + file_management_tools
        super().__init__(
            model = model,
            tools = new_tools,
            prompt_templates = prompt_templates,
            additional_authorized_imports=["*"],
            code_block_tags=("<python>", "</python>"),
            **kwargs
        )
        
    def run(self,
            task: str,
            **kwargs):
        if "return_full_result" in kwargs:
            return_full_result = kwargs.pop("return_full_result")
        else:
            return_full_result = False
        
        result = super().run(task, return_full_result=True, **kwargs)
        self.token_usage["input"] += result.token_usage.input_tokens
        self.token_usage["output"] += result.token_usage.output_tokens
        self.run_logs.append(self.memory.get_full_steps())
        
        if return_full_result:
            return result
        else:
            return result.output
        
    def print_log(self):
        log_dir = os.path.join(self.root_dir, "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_path = os.path.join(log_dir, f"{self.name}.log")
        with open(log_path, "w+") as f:
            pprint(self.run_logs, stream=f, width=1024)
            
        cost_dir = os.path.join(self.root_dir, "cost")
        if not os.path.exists(cost_dir):
            os.makedirs(cost_dir)
        cost_path = os.path.join(cost_dir, f"{self.name}.json")
        with open(cost_path, "w+") as f:
            json.dump(self.token_usage, f, indent=2)
        
        if hasattr(self, "managed_agents") and  len(self.managed_agents.values()) > 0:
            for agent in self.managed_agents.values():
                if isinstance(agent, ExperimentAgent):
                    agent.print_log()

class SimpleAgent(CodeAgent):
    def __init__(self, 
                 model, 
                 root_dir: str,
                 prompt_templates: dict,
                 tools: list[Tool] = [],
                 **kwargs):
        self.root_dir = root_dir
        self.run_logs = []
        
        new_tools = tools + [WriteFileTool(root_dir)]
        
        super().__init__(
            model = model,
            tools = new_tools,
            prompt_templates = prompt_templates,
            additional_authorized_imports=["*"],
            code_block_tags=("<python>", "</python>"),
            **kwargs
        )
        
    def run(self,
            task: str,
            **kwargs):
        super().run(task, **kwargs)
        self.run_logs.append(self.memory.get_full_steps())
        
    def print_log(self):
        log_dir = os.path.join(self.root_dir, "agent_logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_path = os.path.join(log_dir, f"{self.name}.log")
        with open(log_path, "w") as f:
            pprint(self.run_logs, stream=f, width=1024)
        
        if hasattr(self, "managed_agents") and  len(self.managed_agents.values()) > 0:
            for agent in self.managed_agents.values():
                if isinstance(agent, ExperimentAgent):
                    agent.print_log()

def generate_file_management_tools_langchain(root_dir: str) -> list[Tool]:
    toolkit = FileManagementToolkit(
        root_dir=root_dir,
        selected_tools=["list_directory", "read_file", "write_file", "file_delete"]
    )
    tools = [Tool.from_langchain(tool) for tool in toolkit.get_tools()]
    for tool in tools:
        tool.description = tool.description + ". You should not omit the argument name in the tool call."
    return tools


def generate_file_management_tools(root_dir: str) -> list[Tool]:
    tools = [ReadFileTool(root_dir), WriteFileTool(root_dir), ListDirectoryTool(root_dir)]
    for tool in tools:
        tool.description = tool.description + " You should not omit the argument name in the tool call."
    return tools

class BashTool(Tool):
    name = "bash"
    description = "A tool that can run bash commands."
    inputs = {
        "command": {
            "type": "string",
            "description": "The command to run"
        }
    }
    output_type = "string"

    def __init__(self, root_dir: str, env_name: str):
        self.root_dir = root_dir
        self.env_name = env_name
        super().__init__()

    def forward(self, command: str) -> str:
        
        try:
            output = subprocess.run(
                f"conda run -n {self.env_name} {command}",
                timeout=600,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=self.root_dir,
            ).stdout.decode()
        except subprocess.TimeoutExpired:
            raise Exception(f"Command {command} timed out. Please check if there are any errors in the code.")
        except CalledProcessError as error:
            raise Exception(f"Error running command {command}: \n{error.output.decode()}")
        except Exception as error:
            raise Exception(f"Error running command {command}: \n{error}")
            
        return output

class ReadFileTool(Tool):
    name = "read_file"
    description = "A tool that can read files. Please provide the path as a string."
    inputs = {
        "path": {
            "type": "string",
            "description": "The path to the file to read"
        }
    }
    output_type = "string"
    
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        super().__init__()
        
    def forward(self, path: str) -> str:
        full_path = os.path.join(self.root_dir, path)
        try:
            with open(full_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File {path} not found")
        except Exception as e:
            raise Exception(f"Error reading file {path}: \n{e}")

class WriteFileTool(Tool):
    name = "write_file"
    description = "A tool that can write files. Please provide the path and the content as strings."
    inputs = {
        "path": {
            "type": "string",
            "description": "The path to the file to write"
        },
        "content": {
            "type": "string",
            "description": "The content to write to the file"
        }
    }
    output_type = "string"
    
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        super().__init__()
        
    def forward(self, path: str, content: str) -> str:
        try:
            full_path = os.path.join(self.root_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w+") as f:
                f.write(content)
            return f"File {path} written successfully"
        except Exception as e:
            raise Exception(f"Error writing file {path}: \n{e}")

class ListDirectoryTool(Tool):
    name = "list_directory"
    description = "A tool that can list directories. Please provide the path as a string. This tool will return a STRING of the contents of the directory in a multi-line format, not a python list."
    inputs = {
        "path": {
            "type": "string",
            "description": "The path to the directory to list"
        }
    }
    output_type = "string"
    
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        super().__init__()
        
    def forward(self, path: str) -> str:
        full_path = os.path.join(self.root_dir, path)
        try:
            return "\n".join(os.listdir(full_path))
        except FileNotFoundError:
            raise Exception(f"Directory {path} not found")
        except Exception as e:
            e.message = f"Error listing directory {path}: {e}"
            raise Exception(f"Error listing directory {path}: {e}")

def calc_cost(model, input_tokens, output_tokens):
    model_cost = {
        "gpt-4o": {"in": 2.50, "out": 10.00},
        "gpt-4o-mini": {"in": 0.150, "out": 0.6},
        "o1-mini": {"in": 1.1, "out": 4.4},
        "claude-3-5-sonnet": {"in": 3.00, "out": 12.00},
        "deepseek-chat": {"in": 0.3, "out": 1.1},
        "deepseek-r1": {"in": 0.6, "out": 2.2},
        "o1": {"in": 15.00, "out": 60.00},
        "o3-mini": {"in": 1.1, "out": 4.4},
        "deepseek-v3": {"in": 0.28, "out": 0.42},
        "qwen3-480b": {"in": 0.0, "out": 0.0},
    }
    
    return model_cost[model]["in"] * input_tokens / 1_000_000 + model_cost[model]["out"] * output_tokens / 1_000_000
    
    

if __name__ == "__main__":
    tools = generate_file_management_tools("test/")
    print(tools)