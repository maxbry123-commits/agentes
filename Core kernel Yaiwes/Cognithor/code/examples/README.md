# Examples

Practical code samples for extending and integrating with Cognithor.

| File | Description |
|------|-------------|
| [`websocket_client.py`](websocket_client.py) | Connect to the WebUI WebSocket, authenticate, send messages, handle streaming |
| [`api_client.py`](api_client.py) | Interact with the Control Center REST API (health, status, config) |
| [`custom_skill.md`](custom_skill.md) | Template for creating a new procedural skill with YAML frontmatter |

## Running

```bash
# WebSocket client (requires: pip install websockets)
# Start Cognithor first: python -m jarvis --no-cli
python examples/websocket_client.py "Search for Python best practices"

# REST API client (no extra deps)
python examples/api_client.py
```

## Creating a Skill

Copy `custom_skill.md` to your skills directory:

```bash
mkdir -p ~/.jarvis/skills/my-skill
cp examples/custom_skill.md ~/.jarvis/skills/my-skill/skill.md
```

Edit the YAML frontmatter and skill body, then restart Cognithor. The skill
will be automatically discovered by the SkillRegistry.
