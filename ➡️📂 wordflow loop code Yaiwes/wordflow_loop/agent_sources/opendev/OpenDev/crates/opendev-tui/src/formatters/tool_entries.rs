//! Static tool registry and runtime display map.
//!
//! Contains the `TOOL_REGISTRY` array and `lookup_tool()` resolution logic.

use std::collections::HashMap;
use std::sync::OnceLock;

use opendev_tools_core::ToolDisplayMeta;

use super::tool_categories::{ResultFormat, ToolCategory, ToolDisplayEntry, category_from_name};

/// The static registry — single source of truth for all tool display metadata.
pub(crate) static TOOL_REGISTRY: &[ToolDisplayEntry] = &[
    // File I/O
    ToolDisplayEntry {
        names: &["Read", "read_file"],
        category: ToolCategory::FileRead,
        verb: "Read",
        label: "file",
        primary_arg_keys: &["file_path", "path"],
        result_format: ResultFormat::File,
    },
    ToolDisplayEntry {
        names: &["Glob", "list_files"],
        category: ToolCategory::FileRead,
        verb: "List",
        label: "files",
        primary_arg_keys: &["path", "directory", "pattern"],
        result_format: ResultFormat::Directory,
    },
    ToolDisplayEntry {
        names: &["Write", "write_file"],
        category: ToolCategory::FileWrite,
        verb: "Write",
        label: "file",
        primary_arg_keys: &["file_path", "path"],
        result_format: ResultFormat::File,
    },
    ToolDisplayEntry {
        names: &["Edit", "edit_file"],
        category: ToolCategory::FileWrite,
        verb: "Edit",
        label: "file",
        primary_arg_keys: &["file_path", "path"],
        result_format: ResultFormat::File,
    },
    ToolDisplayEntry {
        names: &["NotebookEdit", "notebook_edit"],
        category: ToolCategory::Notebook,
        verb: "Edit",
        label: "notebook",
        primary_arg_keys: &["path", "file_path"],
        result_format: ResultFormat::File,
    },
    // Execution
    ToolDisplayEntry {
        names: &["Bash", "run_command", "bash_execute"],
        category: ToolCategory::Bash,
        verb: "Bash",
        label: "command",
        primary_arg_keys: &["command"],
        result_format: ResultFormat::Bash,
    },
    // Search
    ToolDisplayEntry {
        names: &["Grep", "grep", "search"],
        category: ToolCategory::Search,
        verb: "Grep",
        label: "project",
        primary_arg_keys: &["pattern", "query"],
        result_format: ResultFormat::Directory,
    },
    ToolDisplayEntry {
        names: &["WebSearch", "web_search"],
        category: ToolCategory::Search,
        verb: "Search",
        label: "web",
        primary_arg_keys: &["query", "pattern"],
        result_format: ResultFormat::Generic,
    },
    // Web
    ToolDisplayEntry {
        names: &["WebFetch", "fetch_url", "web_fetch"],
        category: ToolCategory::Web,
        verb: "Fetch",
        label: "url",
        primary_arg_keys: &["url"],
        result_format: ResultFormat::Generic,
    },
    // Multi-Agent
    ToolDisplayEntry {
        names: &["Agent", "spawn_subagent"],
        category: ToolCategory::Agent,
        verb: "Agent",
        label: "subagent",
        primary_arg_keys: &["description"],
        result_format: ResultFormat::Generic,
    },
    ToolDisplayEntry {
        names: &["TeamCreate", "create_team"],
        category: ToolCategory::Agent,
        verb: "Create",
        label: "team",
        primary_arg_keys: &["team_name"],
        result_format: ResultFormat::Generic,
    },
    ToolDisplayEntry {
        names: &["TeamDelete", "delete_team"],
        category: ToolCategory::Agent,
        verb: "Delete",
        label: "team",
        primary_arg_keys: &["team_name"],
        result_format: ResultFormat::Generic,
    },
    ToolDisplayEntry {
        names: &["SendMessage", "send_message"],
        category: ToolCategory::Agent,
        verb: "Send",
        label: "message",
        primary_arg_keys: &["to", "message"],
        result_format: ResultFormat::Generic,
    },
    // Task management
    ToolDisplayEntry {
        names: &["EnterPlanMode", "present_plan"],
        category: ToolCategory::Plan,
        verb: "Plan",
        label: "plan",
        primary_arg_keys: &["name", "title"],
        result_format: ResultFormat::Generic,
    },
    ToolDisplayEntry {
        names: &["TodoWrite", "write_todos"],
        category: ToolCategory::Plan,
        verb: "Todos",
        label: "todos",
        primary_arg_keys: &["name", "title"],
        result_format: ResultFormat::Todo,
    },
    ToolDisplayEntry {
        names: &["TaskUpdate", "update_todo"],
        category: ToolCategory::Plan,
        verb: "Update",
        label: "task",
        primary_arg_keys: &["id", "name"],
        result_format: ResultFormat::Todo,
    },
    ToolDisplayEntry {
        names: &["TaskList", "list_todos"],
        category: ToolCategory::Plan,
        verb: "List",
        label: "tasks",
        primary_arg_keys: &[],
        result_format: ResultFormat::Todo,
    },
    ToolDisplayEntry {
        names: &["TaskStop", "task_complete"],
        category: ToolCategory::Plan,
        verb: "Complete",
        label: "task",
        primary_arg_keys: &["status", "message"],
        result_format: ResultFormat::Generic,
    },
    // User interaction
    ToolDisplayEntry {
        names: &["AskUserQuestion", "ask_user"],
        category: ToolCategory::UserInteraction,
        verb: "Ask",
        label: "user",
        primary_arg_keys: &["question", "message"],
        result_format: ResultFormat::Generic,
    },
    // Meta
    ToolDisplayEntry {
        names: &["Skill", "invoke_skill"],
        category: ToolCategory::Other,
        verb: "Skill",
        label: "skill",
        primary_arg_keys: &["name", "skill"],
        result_format: ResultFormat::Generic,
    },
    ToolDisplayEntry {
        names: &["LSP", "lsp_query"],
        category: ToolCategory::Symbol,
        verb: "LSP",
        label: "query",
        primary_arg_keys: &["action", "file_path"],
        result_format: ResultFormat::Generic,
    },
    // Scheduling
    ToolDisplayEntry {
        names: &["CronCreate", "schedule"],
        category: ToolCategory::Other,
        verb: "Schedule",
        label: "task",
        primary_arg_keys: &["action", "description", "command"],
        result_format: ResultFormat::Generic,
    },
];

/// Default entry for unknown tools.
pub(crate) static DEFAULT_ENTRY: ToolDisplayEntry = ToolDisplayEntry {
    names: &[],
    category: ToolCategory::Other,
    verb: "Call",
    label: "",
    primary_arg_keys: &[
        "command",
        "file_path",
        "path",
        "url",
        "query",
        "pattern",
        "name",
    ],
    result_format: ResultFormat::Generic,
};

/// MCP fallback entry.
static MCP_ENTRY: ToolDisplayEntry = ToolDisplayEntry {
    names: &[],
    category: ToolCategory::Mcp,
    verb: "MCP",
    label: "tool",
    primary_arg_keys: &[
        "command",
        "file_path",
        "path",
        "url",
        "query",
        "pattern",
        "name",
    ],
    result_format: ResultFormat::Generic,
};

/// Docker fallback entry.
static DOCKER_ENTRY: ToolDisplayEntry = ToolDisplayEntry {
    names: &[],
    category: ToolCategory::Docker,
    verb: "Docker",
    label: "operation",
    primary_arg_keys: &["command", "container", "image", "name"],
    result_format: ResultFormat::Generic,
};

/// Runtime display entries populated from tool `display_meta()` implementations.
/// Provides a fallback for tools not in the static registry.
static RUNTIME_DISPLAY: OnceLock<HashMap<String, ToolDisplayEntry>> = OnceLock::new();

/// Initialize the runtime display map from tool metadata.
///
/// Call this once after tool registration. Only the first call takes effect.
pub fn init_runtime_display(map: HashMap<String, ToolDisplayMeta>) {
    let entries: HashMap<String, ToolDisplayEntry> = map
        .into_iter()
        .map(|(name, meta)| {
            let entry = ToolDisplayEntry {
                names: &[],
                category: category_from_name(meta.category),
                verb: meta.verb,
                label: meta.label,
                primary_arg_keys: meta.primary_arg_keys,
                result_format: ResultFormat::Generic,
            };
            (name, entry)
        })
        .collect();
    let _ = RUNTIME_DISPLAY.set(entries);
}

/// Look up a tool's display metadata by name.
///
/// Resolution order:
/// 1. Static `TOOL_REGISTRY` exact match
/// 2. Runtime display map (from tool `display_meta()`)
/// 3. Prefix fallbacks (`mcp__*`, `docker_*`)
/// 4. `DEFAULT_ENTRY`
pub fn lookup_tool(name: &str) -> &ToolDisplayEntry {
    // 1. Exact match in static registry
    for entry in TOOL_REGISTRY {
        if entry.names.contains(&name) {
            return entry;
        }
    }

    // 2. Runtime display map (from tool display_meta() implementations)
    if let Some(rt) = RUNTIME_DISPLAY.get()
        && let Some(entry) = rt.get(name)
    {
        return entry;
    }

    // 3. Prefix fallbacks
    if name.starts_with("mcp__") {
        return &MCP_ENTRY;
    }
    if name.starts_with("docker_") {
        return &DOCKER_ENTRY;
    }

    &DEFAULT_ENTRY
}
