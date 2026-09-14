"""Parallel tool execution policy.

Defines which tools can safely run in parallel (read-only or isolated writes)
and which must be executed sequentially (state-mutating).
"""

from __future__ import annotations

import re

# Tools that are SAFE to parallelize (read-only or isolated writes)
PARALLELIZABLE: frozenset[str] = frozenset(
    {
        "web_search",
        "web_news_search",
        "search_and_read",
        "web_fetch",
        "http_request",
        "read_file",
        "list_directory",
        "search_files",
        "find_in_files",
        "search_memory",
        "get_core_memory",
        "get_recent_episodes",
        "search_procedures",
        "memory_stats",
        "get_entity",
        "vault_search",
        "vault_read",
        "vault_list",
        "knowledge_synthesize",
        "knowledge_gaps",
        "knowledge_contradictions",
        "knowledge_timeline",
        "analyze_document",
        "read_pdf",
        "read_docx",
        "read_ppt",
        "analyze_code",
        "git_status",
        "git_diff",
        "git_log",
        "db_query",
        "db_schema",
        "docker_ps",
        "docker_logs",
        "docker_inspect",
        "list_skills",
        "email_read_inbox",
        "email_search",
        "email_summarize",
        "calendar_today",
        "calendar_upcoming",
        "calendar_check_availability",
        "list_reminders",
        "get_clipboard",
        "screenshot_desktop",
        "screenshot_region",
        "api_list",
        "browser_extract",
        "browser_analyze",
        "browser_screenshot",
        "chart_from_csv",
        "media_extract_text",
        "media_analyze_image",
    }
)

# Tools that must be SEQUENTIAL (state-mutating)
SEQUENTIAL_ONLY: frozenset[str] = frozenset(
    {
        "write_file",
        "edit_file",
        "find_and_replace",
        "exec_command",
        "run_python",
        "save_to_memory",
        "add_entity",
        "add_relation",
        "vault_save",
        "vault_update",
        "vault_link",
        "document_export",
        "git_commit",
        "git_branch",
        "db_execute",
        "db_connect",
        "docker_run",
        "docker_stop",
        "email_send",
        "calendar_create_event",
        "set_reminder",
        "send_notification",
        "set_clipboard",
        "create_skill",
        "record_procedure_usage",
        "browser_navigate",
        "browser_click",
        "browser_fill",
        "browser_fill_form",
        "browser_execute_js",
        "browser_key",
        "browser_tab",
        "cognithor_resume",
        "install_community_skill",
        "report_skill",
        "media_tts",
        "media_resize_image",
        "media_convert_audio",
        "media_transcribe_audio",
        "create_chart",
        "create_table_image",
        "api_connect",
        "api_call",
        "api_disconnect",
    }
)

# Pattern for MCP read tools from external servers
_MCP_READ_PATTERN = re.compile(r"^mcp_.*_read$")


def is_parallelizable(tool_name: str) -> bool:
    """Return True if the tool can safely run in parallel."""
    if tool_name in PARALLELIZABLE:
        return True
    if tool_name in SEQUENTIAL_ONLY:
        return False
    # MCP read pattern
    if _MCP_READ_PATTERN.match(tool_name):
        return True
    # Unknown tools default to sequential for safety
    return False
