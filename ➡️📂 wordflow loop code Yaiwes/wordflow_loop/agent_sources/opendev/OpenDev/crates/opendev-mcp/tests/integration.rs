//! Integration tests for the MCP client.
//!
//! Tests MCP model serialization, JSON-RPC protocol types, manager lifecycle,
//! and the full mock server flow (initialize handshake, tools/list, tool call).

use std::collections::HashMap;
use std::path::PathBuf;

use opendev_mcp::models::{
    JsonRpcNotification, JsonRpcRequest, JsonRpcResponse, McpContent, McpTool, McpToolResult,
    McpToolSchema,
};
use opendev_mcp::{McpError, McpManager, McpServerConfig, TransportType};

// ========================================================================
// JSON-RPC protocol types
// ========================================================================

/// JsonRpcRequest serializes correctly with all fields.
#[test]
fn jsonrpc_request_serialization() {
    let mut params = HashMap::new();
    params.insert("name".to_string(), serde_json::json!("greet"));
    params.insert(
        "arguments".to_string(),
        serde_json::json!({"name": "world"}),
    );

    let req = JsonRpcRequest {
        jsonrpc: "2.0".to_string(),
        id: 42,
        method: "tools/call".to_string(),
        params: Some(params),
    };

    let json = serde_json::to_string(&req).unwrap();
    let parsed: serde_json::Value = serde_json::from_str(&json).unwrap();

    assert_eq!(parsed["jsonrpc"], "2.0");
    assert_eq!(parsed["id"], 42);
    assert_eq!(parsed["method"], "tools/call");
    assert_eq!(parsed["params"]["name"], "greet");
    assert_eq!(parsed["params"]["arguments"]["name"], "world");
}

/// JsonRpcRequest without params omits the params field.
#[test]
fn jsonrpc_request_no_params_omitted() {
    let req = JsonRpcRequest {
        jsonrpc: "2.0".to_string(),
        id: 1,
        method: "tools/list".to_string(),
        params: None,
    };

    let json = serde_json::to_string(&req).unwrap();
    assert!(!json.contains("params"));
}

/// JsonRpcNotification has no id field.
#[test]
fn jsonrpc_notification_has_no_id() {
    let notif = JsonRpcNotification {
        jsonrpc: "2.0".to_string(),
        method: "notifications/initialized".to_string(),
        params: None,
    };

    let json = serde_json::to_string(&notif).unwrap();
    assert!(!json.contains("\"id\""));
    assert!(json.contains("notifications/initialized"));
}

/// JsonRpcResponse with result deserializes correctly.
#[test]
fn jsonrpc_response_with_result() {
    let json = r#"{
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "test", "version": "1.0"}
        }
    }"#;

    let resp: JsonRpcResponse = serde_json::from_str(json).unwrap();
    assert_eq!(resp.id, Some(1));
    assert!(resp.result.is_some());
    assert!(resp.error.is_none());
    assert_eq!(resp.result.unwrap()["serverInfo"]["name"], "test");
}

/// JsonRpcResponse with error deserializes correctly.
#[test]
fn jsonrpc_response_with_error() {
    let json = r#"{
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "code": -32601,
            "message": "Method not found"
        }
    }"#;

    let resp: JsonRpcResponse = serde_json::from_str(json).unwrap();
    assert!(resp.result.is_none());
    let err = resp.error.unwrap();
    assert_eq!(err.code, -32601);
    assert_eq!(err.message, "Method not found");
}

// ========================================================================
// MCP model types
// ========================================================================

/// McpTool serialization roundtrip preserves all fields.
#[test]
fn mcp_tool_roundtrip() {
    let tool = McpTool {
        name: "read_file".to_string(),
        description: "Read a file from disk".to_string(),
        input_schema: serde_json::json!({
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"}
            },
            "required": ["path"]
        }),
    };

    let json = serde_json::to_string(&tool).unwrap();
    let deserialized: McpTool = serde_json::from_str(&json).unwrap();

    assert_eq!(deserialized.name, "read_file");
    assert_eq!(deserialized.description, "Read a file from disk");
    assert_eq!(deserialized.input_schema["required"][0], "path");
}

/// McpContent text and image variants serialize with correct type tags.
#[test]
fn mcp_content_type_tags() {
    let text = McpContent::Text {
        text: "Hello world".to_string(),
    };
    let json = serde_json::to_string(&text).unwrap();
    assert!(json.contains(r#""type":"text""#));
    assert!(json.contains("Hello world"));

    let image = McpContent::Image {
        data: "aGVsbG8=".to_string(),
        mime_type: "image/png".to_string(),
    };
    let json = serde_json::to_string(&image).unwrap();
    assert!(json.contains(r#""type":"image""#));
    assert!(json.contains("image/png"));
}

/// McpToolResult correctly models success and error cases.
#[test]
fn mcp_tool_result_success_and_error() {
    let success = McpToolResult {
        content: vec![McpContent::Text {
            text: "result data".to_string(),
        }],
        is_error: false,
    };
    assert!(!success.is_error);
    assert_eq!(success.content.len(), 1);

    let error = McpToolResult {
        content: vec![McpContent::Text {
            text: "Something went wrong".to_string(),
        }],
        is_error: true,
    };
    assert!(error.is_error);
}

/// McpToolSchema correctly namespaces tool names.
#[test]
fn mcp_tool_schema_namespacing() {
    let schema = McpToolSchema {
        name: "sqlite__query".to_string(),
        description: "Run a SQL query".to_string(),
        parameters: serde_json::json!({
            "type": "object",
            "properties": {"sql": {"type": "string"}}
        }),
        server_name: "sqlite".to_string(),
        original_name: "query".to_string(),
    };

    assert_eq!(schema.name, "sqlite__query");
    assert_eq!(schema.server_name, "sqlite");
    assert_eq!(schema.original_name, "query");
}

// ========================================================================
// McpManager basic operations
// ========================================================================

/// Manager starts with zero connections.
#[tokio::test]
async fn manager_starts_empty() {
    let manager = McpManager::new(None);
    assert_eq!(manager.connected_count().await, 0);
    assert!(manager.list_servers().await.is_empty());
    assert!(manager.get_all_tool_schemas().await.is_empty());
}

/// Connecting to a nonexistent server returns ServerNotFound error.
#[tokio::test]
async fn connect_nonexistent_server_returns_error() {
    let manager = McpManager::new(Some(PathBuf::from("/tmp")));
    // Set empty config so the manager doesn't try to load from disk
    manager
        .add_server(
            "other".to_string(),
            McpServerConfig {
                command: "echo".to_string(),
                args: vec![],
                ..Default::default()
            },
        )
        .await
        .unwrap();

    let result = manager.connect_server("nonexistent").await;
    assert!(matches!(result, Err(McpError::ServerNotFound(_))));
}

/// Disconnecting from a nonexistent server returns ServerNotFound.
#[tokio::test]
async fn disconnect_nonexistent_server_returns_error() {
    let manager = McpManager::new(None);
    let result = manager.disconnect_server("ghost").await;
    assert!(matches!(result, Err(McpError::ServerNotFound(_))));
}

/// Add and remove server configurations.
#[tokio::test]
async fn add_and_remove_server_config() {
    let manager = McpManager::new(Some(PathBuf::from("/tmp")));

    manager
        .add_server(
            "test-srv".to_string(),
            McpServerConfig {
                command: "node".to_string(),
                args: vec!["server.js".to_string()],
                transport: TransportType::Stdio,
                enabled: true,
                auto_start: false,
                ..Default::default()
            },
        )
        .await
        .unwrap();

    let config = manager.get_config().await.unwrap();
    assert!(config.mcp_servers.contains_key("test-srv"));

    manager.remove_server("test-srv").await.unwrap();
    let config = manager.get_config().await.unwrap();
    assert!(!config.mcp_servers.contains_key("test-srv"));
}

/// is_connected returns false for unknown servers.
#[tokio::test]
async fn is_connected_false_for_unknown() {
    let manager = McpManager::new(None);
    assert!(!manager.is_connected("unknown").await);
}

// ========================================================================
// Full lifecycle with mock MCP server
// ========================================================================

/// Full integration test: connect to a Python mock MCP server, run
/// initialize handshake, discover tools, call a tool, then disconnect.
#[tokio::test]
async fn full_lifecycle_mock_server_initialize_discover_call_disconnect() {
    // Check if python3 is available
    let python_check = std::process::Command::new("python3")
        .arg("--version")
        .output();
    if python_check.is_err() || !python_check.unwrap().status.success() {
        // Skip test if python3 is not available
        return;
    }

    let script = r#"
import sys, json

def read_message():
    while True:
        line = sys.stdin.readline()
        if not line:
            return None
        if line.startswith("Content-Length:"):
            length = int(line.split(":")[1].strip())
            sys.stdin.readline()  # blank line
            body = sys.stdin.read(length)
            return json.loads(body)

def write_message(obj):
    body = json.dumps(obj)
    sys.stdout.write(f"Content-Length: {len(body)}\r\n\r\n{body}")
    sys.stdout.flush()

while True:
    msg = read_message()
    if msg is None:
        break
    if "id" not in msg:
        continue  # notification
    method = msg.get("method", "")
    if method == "initialize":
        write_message({
            "jsonrpc": "2.0",
            "id": msg["id"],
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "test-server", "version": "0.1.0"}
            }
        })
    elif method == "tools/list":
        write_message({
            "jsonrpc": "2.0",
            "id": msg["id"],
            "result": {
                "tools": [
                    {
                        "name": "echo",
                        "description": "Echo back input",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"message": {"type": "string"}},
                            "required": ["message"]
                        }
                    },
                    {
                        "name": "add",
                        "description": "Add two numbers",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"a": {"type": "number"}, "b": {"type": "number"}}
                        }
                    }
                ]
            }
        })
    elif method == "tools/call":
        tool_name = msg["params"]["name"]
        args = msg["params"].get("arguments", {})
        if tool_name == "echo":
            text = args.get("message", "")
            write_message({
                "jsonrpc": "2.0",
                "id": msg["id"],
                "result": {
                    "content": [{"type": "text", "text": f"Echo: {text}"}],
                    "isError": False
                }
            })
        elif tool_name == "add":
            result = args.get("a", 0) + args.get("b", 0)
            write_message({
                "jsonrpc": "2.0",
                "id": msg["id"],
                "result": {
                    "content": [{"type": "text", "text": str(result)}],
                    "isError": False
                }
            })
        else:
            write_message({
                "jsonrpc": "2.0",
                "id": msg["id"],
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
            })
    else:
        write_message({
            "jsonrpc": "2.0",
            "id": msg["id"],
            "error": {"code": -32601, "message": "Method not found"}
        })
"#;

    let manager = McpManager::new(Some(PathBuf::from("/tmp")));

    // Configure mock server
    manager
        .add_server(
            "mock".to_string(),
            McpServerConfig {
                command: "python3".to_string(),
                args: vec!["-c".to_string(), script.to_string()],
                transport: TransportType::Stdio,
                enabled: true,
                auto_start: true,
                ..Default::default()
            },
        )
        .await
        .unwrap();

    // 1. Connect (runs initialize handshake + tools/list)
    manager.connect_server("mock").await.unwrap();
    assert!(manager.is_connected("mock").await);
    assert_eq!(manager.connected_count().await, 1);

    // 2. Verify tools were discovered
    let schemas = manager.get_all_tool_schemas().await;
    assert_eq!(schemas.len(), 2, "should discover 2 tools");
    let echo_schema = schemas.iter().find(|s| s.original_name == "echo").unwrap();
    assert_eq!(echo_schema.name, "mock__echo");
    assert_eq!(echo_schema.description, "Echo back input");
    assert_eq!(echo_schema.server_name, "mock");

    let add_schema = schemas.iter().find(|s| s.original_name == "add").unwrap();
    assert_eq!(add_schema.name, "mock__add");

    // 3. Call the echo tool
    let result = manager
        .call_tool("mock", "echo", serde_json::json!({"message": "hello"}))
        .await
        .unwrap();
    assert!(!result.is_error);
    assert_eq!(result.content.len(), 1);

    // 4. Call the add tool
    let result = manager
        .call_tool("mock", "add", serde_json::json!({"a": 3, "b": 7}))
        .await
        .unwrap();
    assert!(!result.is_error);

    // 5. List servers
    let servers = manager.list_servers().await;
    assert_eq!(servers.len(), 1);
    assert_eq!(servers[0].name, "mock");
    assert!(servers[0].connected);
    assert_eq!(servers[0].tools.len(), 2);

    // 6. Disconnect
    manager.disconnect_server("mock").await.unwrap();
    assert!(!manager.is_connected("mock").await);
    assert_eq!(manager.connected_count().await, 0);
}

/// Calling a tool on a disconnected server returns an error.
#[tokio::test]
async fn call_tool_on_disconnected_server_errors() {
    let manager = McpManager::new(None);
    let result = manager
        .call_tool("nonexistent", "tool", serde_json::json!({}))
        .await;
    assert!(matches!(result, Err(McpError::ServerNotFound(_))));
}
