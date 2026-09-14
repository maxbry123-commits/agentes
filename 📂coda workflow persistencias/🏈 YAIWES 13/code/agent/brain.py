import json
from typing import List, Dict
from openai import OpenAI
from agent.tools_schema import get_tools_description, Action
from config import LLMConfig
import re

JSON_INSTRUCTIONS = """
RESPONSE FORMAT:
You MUST respond with a valid JSON object in the following format:
{
    "reasoning": "Explain your thought process here...",
    "tool_name": "exact_tool_name_from_list",
    "arguments": "arguments_string"
}

EXAMPLE:
{
    "reasoning": "I need to scan the target to find open ports.",
    "tool_name": "nmap",
    "arguments": "-F 192.168.1.1"
}
"""

class Brain:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = OpenAI(
            base_url=self.config.base_url,
            api_key=self.config.api_key
        )
        self.system_prompt = self._build_system_prompt()

    def update_system_prompt(self, new_prompt: str):
        """Dynamic prompt swapping for Multi-Agent support."""
        self.system_prompt = new_prompt + "\n" + get_tools_description() + "\n" + JSON_INSTRUCTIONS

    def _build_system_prompt(self):
        return f"""You are an autonomous penetration testing agent.
Your goal is to methodically discover vulnerabilities and exploit the target.

{get_tools_description()}

RESPONSE FORMAT:
You MUST respond with a valid JSON object in the following format:
{{
    "reasoning": "Explain your thought process here...",
    "tool_name": "exact_tool_name_from_list",
    "arguments": "arguments_string"
}}

EXAMPLE:
{{
    "reasoning": "I need to scan the target to find open ports.",
    "tool_name": "nmap",
    "arguments": "-F 192.168.1.1"
}}

GUIDELINES:
1. Start with Reconnaissance (nmap).
2. Analyze results carefully.
3. If you find a web server, check for directories (gobuster).
4. If you find a version, search for exploits (searchsploit).
5. Do not repeat the same failed command endlessly.
"""

    def get_next_action(self, history: List[Dict]) -> Action:
        """
        Decide the next action based on execution history.
        """
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add recent history (pruning implementation would go here)
        # For small models, we might just take the last 3 steps to save context
        recent_history = history[-3:] if len(history) > 3 else history
        
        for entry in recent_history:
            if entry["type"] == "action":
                content = entry["content"]
                msg = f"My Action: Ran {content.get('tool')} with {content.get('args')}"
                messages.append({"role": "user", "content": msg})
            elif entry["type"] == "output":
                # Truncate content for the model input
                out = str(entry["content"])[:2000] 
                messages.append({"role": "user", "content": f"Result:\n{out}"})

        messages.append({"role": "user", "content": "What is the next step? Respond in JSON."})

        try:
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                response_format={"type": "json_object"}, 
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            # Basic cleanup if model adds markdown blocks
            content = content.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(content)
            return Action(**data)
        except Exception as e:
            print(f"[!] Brain Error: {e}")
            # Fallback or retry logic could go here
            return Action(
                tool_name="error",
                arguments="",
                reasoning=f"Failed to generate action: {str(e)}"
            )
