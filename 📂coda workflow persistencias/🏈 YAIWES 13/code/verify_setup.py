import sys
from config import load_config
from agent.executor import SSHExecutor
from agent.brain import Brain

def verify():
    print("[-] Loading Config...")
    try:
        config = load_config()
        print("[+] Config Loaded.")
    except Exception as e:
        print(f"[!] Config Error: {e}")
        return

    print(f"[-] Testing SSH to {config.ssh.hostname}...")
    exc = SSHExecutor(
        hostname=config.ssh.hostname, 
        port=config.ssh.port, 
        username=config.ssh.username,
        password=config.ssh.password,
        key_filename=config.ssh.key_filename
    )
    if exc.connect():
        print("[+] SSH Connection Successful.")
        out, err, _ = exc.run_command("id")
        print(f"    output: {out}")
        exc.close()
    else:
        print("[!] SSH Connection Failed.")

    print(f"[-] Testing Brain (LLM) at {config.llm.base_url}...")
    try:
        brain = Brain(config.llm)
        print("[+] Brain initialized.")
        
        from agent.agents import AgentManager
        am = AgentManager(brain)
        print("[+] AgentManager initialized.")
        
        from agent.memory import MemoryHelper
        mem = MemoryHelper(persist_dir="test_memory")
        print("[+] RAG Memory initialized (Chromadb).")
        
        from agent.web import WebAnalyzer
        print("[+] WebAnalyzer module loaded.")
        
    except Exception as e:
        print(f"[!] Component Init Failed: {e}")

if __name__ == "__main__":
    verify()
