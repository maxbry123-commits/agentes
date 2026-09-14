import argparse
import sys
import time
from config import load_config
from agent.executor import SSHExecutor
from agent.brain import Brain
from agent.logger import SessionLogger, OutputParser
from agent.tools_schema import NAIVE_TOOLS
from agent.memory import MemoryHelper
from agent.web import WebAnalyzer
from agent.agents import AgentManager

def main():
    parser = argparse.ArgumentParser(description="Pentesting AI Agent")
    parser.add_argument("--target", required=True, help="Target IP address")
    parser.add_argument("--max-steps", type=int, default=30, help="Maximum steps to run")
    args = parser.parse_args()

    # Load Config
    config = load_config()
    
    # Initialize Logger
    logger = SessionLogger()
    print(f"[*] Session ID: {logger.session_id}")
    
    # Initialize Memory (RAG)
    memory = MemoryHelper(
        persist_dir=config.memory.persist_dir,
        collection_name=config.memory.collection_name
    )
    memory.clear() 
    print("[*] RAG Memory Initialized.")

    # Initialize Executor
    print(f"[*] Connecting to Kali ({config.ssh.hostname})...")
    executor = SSHExecutor(
        hostname=config.ssh.hostname,
        port=config.ssh.port,
        username=config.ssh.username,
        password=config.ssh.password,
        key_filename=config.ssh.key_filename
    )
    
    if not executor.connect():
        print("[!] Failed to connect to Kali. Check credentials.")
        sys.exit(1)

    # Initialize Web Analyzer
    web_analyzer = WebAnalyzer(executor)

    # Initialize Brain & Agent Manager
    brain = Brain(config.llm)
    agent_manager = AgentManager(brain)
    
    # Set initial agent
    agent_manager.switch_agent("Manager")
    
    # Main Loop
    step_count = 0
    
    print(f"[*] Starting Pentest against {args.target}")
    
    while step_count < args.max_steps:
        current_agent = agent_manager.current_agent
        print(f"\n--- Step {step_count + 1} [{current_agent}] ---")
        
        # 1. Decide
        try:
            print("[*] Brain is thinking...")
            # Retrieve context (for simplicity, we pass history. Real impl would query RAG here)
            action = brain.get_next_action(logger.history)
            
            logger.log_step("thought", action.reasoning)
            memory.add_finding(f"Agent: {current_agent}\nThought: {action.reasoning}", meta={"type": "thought", "step": step_count})
            
            print(f"[?] Thought: {action.reasoning}")
            print(f"[>] Action: {action.tool_name} {action.arguments}")
            
        except Exception as e:
            print(f"[!] Brain Error: {e}")
            break
            
        # 2. Handle Delegation or Execution
        if action.tool_name == "error":
            logger.log_step("action", {"tool": "error", "reason": action.reasoning})
            output_data = f"System Error: {action.reasoning}. Please correctly format your JSON response."
            print(f"[!] {output_data}")

        elif action.tool_name == "delegate":
            target_agent = action.arguments
            if agent_manager.switch_agent(target_agent):
                msg = f"Delegating control to {target_agent}"
                print(f"[*] {msg}")
                logger.log_step("action", {"tool": "delegate", "args": target_agent})
                # Add a system event to history/memory so the new agent knows what happened
                memory.add_finding(f"Manager delegated task to {target_agent}", meta={"type": "delegate", "step": step_count})
                # We skip execution and continue loop, leaving 'output' empty effectively aka next turn
                # But we should probably log an output for the delegation
                logger.log_step("output", f"Switched to {target_agent}")
                step_count += 1
                continue
            else:
                print(f"[!] Failed to switch to agent: {target_agent}")
                output_data = "Error: Invalid Agent Name."
                # Fallthrough to log output
        
        else:
            # Execute Tool
            tool = next((t for t in NAIVE_TOOLS if t.name == action.tool_name), None)
            
            output_data = ""
            if tool:
                # Handle Internal Tools
                if tool.name == "web_inspect":
                    url = action.arguments
                    if args.target not in url and "http" in url:
                        pass
                    print(f"[$] Running Web Inspector on {url}")
                    web_data = web_analyzer.inspect_page(url)
                    output_data = WebAnalyzer.format_for_llm(web_data)
                    
                else:
                    # Generic Tool template filling
                    cmd = tool.command_template
                    final_cmd = ""
                    try:
                        if tool.name == "shell_command":
                            final_cmd = action.arguments
                        elif "{" in cmd:
                            final_cmd = cmd.format(
                                target=args.target, 
                                query=action.arguments, 
                                command=action.arguments,
                                username=config.ssh.username,
                                password=config.ssh.password
                            )
                        else:
                            final_cmd = f"{cmd} {action.arguments}" 
                    except Exception as e:
                         print(f"[!] Exec Error: {e}")
                         final_cmd = f"{cmd} {action.arguments}"

                    logger.log_step("action", {"tool": action.tool_name, "args": action.arguments, "cmd": final_cmd})
                    
                    print(f"[$] Executing: {final_cmd}")
                    stdout, stderr, code = executor.run_command(final_cmd)
                    output_data = stdout if stdout else stderr
            else:
                output_data = f"Tool {action.tool_name} not found."
                print(f"[!] {output_data}")

        # 3. Log Output & Store in Memory
        print(f"[<] Output len: {len(output_data)} chars")
        
        parsed_output = output_data
        if action.tool_name == "nmap":
            parsed_output = OutputParser.parse_nmap(output_data)
        
        logger.log_step("output", parsed_output, meta={"raw_length": len(output_data)})
        
        if len(output_data) > 20 and "command not found" not in output_data:
             memory.add_finding(
                 f"Agent: {current_agent}\nTool: {action.tool_name}\nOutput: {parsed_output}", 
                 meta={"tool": action.tool_name, "step": step_count}
             )
        
        step_count += 1
        time.sleep(2)
    
    print("\n[*] max steps reached or finished.")
    executor.close()

if __name__ == "__main__":
    main()
