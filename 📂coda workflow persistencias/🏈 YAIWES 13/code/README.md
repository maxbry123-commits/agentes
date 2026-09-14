# AI Pentest Agent

An autonomous penetration testing agent designed to orchestrate security assessments using **Local LLMs** or **LLM API's** and a **Kali Linux** execution environment.

## Overview

The Pentest Agent automates the reconnaissance and initial exploitation phases of a penetration test. It adheres to a **Manager-Specialist** multi-agent architecture, where a high-level manager delegates tasks to specialized sub-agents.

### Key Features

*   **Multi-Agent Architecture**:
    *   **Manager**: Strategic planning and task delegation.
    *   **ReconAgent**: Network discovery (Nmap, Masscan).
    *   **WebAgent**: Web application analysis (Gobuster, Nikto, SQLMap).
    *   **ExploitAgent**: Vulnerability research and exploitation (Searchsploit, Metasploit, SSH).
*   **RAG Memory**: Persistent context storage using **ChromaDB** allows the agent to recall findings from previous steps.
*   **Local LLM Support**: Fully compatible with local models via Ollama (recommended: `qwen2.5:1.5b` or `llama3.2:1b`).
*   **Dockerized**: Fully containerized environment for reproducibility.

## Architecture

1.  **Orchestrator (Host)**: Python application that manages the agent loop, memory, and LLM communication.
2.  **Execution Environment (Target)**: The agent connects via SSH to a Kali Linux machine (or container) to execute security tools.
3.  **Inference Engine**: Connects to an OpenAI-compatible API endpoint (e.g., Ollama running on `host.docker.internal`).

## Prerequisites

*   Docker Engine & Docker Compose
*   Ollama (running locally) (optional)
*   Network access to a target machine (or a local vulnerable VM like Metasploitable for testing purposes)

## Configuration

1.  **Clone the Repository**:
    ```bash
    This repo is not production ready.
    ```

2.  **Setup Environment Variables**:
    Copy the example configuration:
    ```bash
    cp .env.example .env
    ```
    Edit `.env` to match your infrastructure:
    *   `TARGET_IP`: The IP address of the system you want to test.
    *   `KALI_HOST`: IP/Hostname of your Kali Linux box.
    *   `KALI_USER` / `KALI_PASS`: SSH credentials for the Kali box.
    *   `LLM_BASE_URL`: URL of your LLM API (e.g., `http://host.docker.internal:11434/v1`).

3.  **Pull the Model**:
    Ensure your Ollama instance has the required model:
    ```bash
    ollama pull qwen2.5:1.5b
    ```

## Usage

Start the agent using the helper script:

```bash
./run.sh
```

Or manually via Docker Compose:

```bash
docker compose up --build
```

### Logs and Output

*   **Console Output**: Displays real-time thoughts and actions of the agents.
*   **Session Logs**: Stored in `logs/session_<timestamp>.md`.
*   **Memory**: Vector database stored in `memory_db/`.

## Disclaimer

This tool is for **educational and authorized security testing purposes only**. Usage of this tool for attacking targets without prior mutual consent is illegal. The developers assume no liability and are not responsible for any misuse or damage caused by this program. You are free to modify this tool according to your needs.
