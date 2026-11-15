from typing import List, Optional
from pydantic import BaseModel, Field

class Tool(BaseModel):
    name: str
    description: str
    command_template: str

class Action(BaseModel):
    tool_name: str = Field(..., description="Name of the tool to use")
    arguments: str = Field("", description="Arguments for the tool")
    reasoning: str = Field(..., description="Reasoning for the action")

# Predefined Tool Definitions
NAIVE_TOOLS = [
    Tool(
        name="nmap",
        description="Network scanner to discover open ports and services.",
        command_template="nmap -sV -p- -T4 {target}"
    ),
    Tool(
        name="gobuster",
        description="Directory brute-forcing tool to find hidden paths on web servers.",
        command_template="gobuster dir -u http://{target} -w /usr/share/wordlists/dirb/common.txt -t 50"
    ),
    Tool(
        name="searchsploit",
        description="Search for exploits for a specific service name or version.",
        command_template="searchsploit {query}"
    ),
    Tool(
        name="ssh_login",
        description="Attempt SSH login with credentials.",
        command_template="sshpass -p '{password}' ssh -o StrictHostKeyChecking=no {username}@{target}"
    ),
    Tool(
        name="web_inspect",
        description="Inspect a URL for forms/inputs (internal tool).",
        command_template="INTERNAL:WEB_INSPECT:{target}" 
    ),
    Tool(
        name="nikto",
        description="Web server scanner for dangerous files/CGIs.",
        command_template="nikto -h {target} -Tuning 123b"
    ),
    Tool(
        name="sqlmap",
        description="Automated SQL injection tool. Use if you found a parameter.",
        command_template="sqlmap -u {target} --batch --smart"
    ),
    Tool(
        name="shell_command",
        description="Run a raw shell command. Use this for specific exploits or navigation.",
        command_template="{command}"
    )
]

def get_tools_description() -> str:
    desc = "Available Tools:\n"
    for tool in NAIVE_TOOLS:
        desc += f"- {tool.name}: {tool.description}\n"
    return desc
