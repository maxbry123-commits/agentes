"""Module-level entrypoint so `python -m backend.apps.reddit_mcp_shim` works."""
from backend.apps.reddit_mcp_shim.server import main

if __name__ == "__main__":
    main()
