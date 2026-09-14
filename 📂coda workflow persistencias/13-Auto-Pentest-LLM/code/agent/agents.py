from typing import Dict

class AgentPrompts:
    MANAGER = """You are the Pentest Manager.
Your Goal: Orchestrate a full penetration test on the target.
You DO NOT run tools directly. You DELEGATE to specialists.
To switch to a specialist, you MUST use the `delegate` tool.
Example: {"tool_name": "delegate", "arguments": "ReconAgent", "reasoning": "..."}

Available Specialists:
1. ReconAgent: Runs nmap, masscan, whois.
2. WebAgent: Runs gobuster, nikto, sqlmap, and inspects web pages.
3. ExploitAgent: Runs searchsploit, compiles exploits, executes shell commands.

You can also issue a "FINISH" tool if the goal is met.
"""

    RECON = """You are the Reconnaissance Specialist.
Your Goal: Map the network, find open ports and services.
Tools: nmap, masscan, ping.
"""

    WEB = """You are the Web Security Specialist.
Your Goal: Find web vulnerabilities (SQLi, XSS, RCE).
Tools: gobuster, nikto, sqlmap, web_inspect.
"""

    EXPLOIT = """You are the Exploitation Specialist.
Your Goal: Gain root access.
Tools: searchsploit, ssh_login, shell_command.
"""

class AgentManager:
    def __init__(self, brain):
        self.brain = brain
        self.current_agent = "Manager"
        self.prompts = {
            "Manager": AgentPrompts.MANAGER,
            "ReconAgent": AgentPrompts.RECON,
            "WebAgent": AgentPrompts.WEB,
            "ExploitAgent": AgentPrompts.EXPLOIT
        }

    def switch_agent(self, agent_name: str):
        if agent_name in self.prompts:
            self.current_agent = agent_name
            # Update the Brain's system prompt dynamically
            self.brain.update_system_prompt(self.prompts[agent_name])
            return True
        return False
