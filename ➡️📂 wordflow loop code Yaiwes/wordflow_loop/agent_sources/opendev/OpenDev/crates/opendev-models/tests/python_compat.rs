//! Compatibility test: verify Rust can deserialize Python-generated session JSON.

use opendev_models::file_change::FileChangeType;
use opendev_models::message::Role;
use opendev_models::session::Session;

const PYTHON_SESSION_JSON: &str = include_str!("python_session_sample.json");

#[test]
fn test_deserialize_python_session() {
    let session: Session = serde_json::from_str(PYTHON_SESSION_JSON)
        .expect("Failed to deserialize Python session JSON");

    assert_eq!(session.id, "test12345678");
    assert_eq!(session.channel, "cli");
    assert_eq!(session.chat_type, "direct");
    assert_eq!(
        session.working_directory,
        Some("/home/user/project".to_string())
    );
    assert_eq!(session.slug, Some("test-session".to_string()));
    assert!(!session.is_archived());
}

#[test]
fn test_python_session_messages() {
    let session: Session = serde_json::from_str(PYTHON_SESSION_JSON).unwrap();

    assert_eq!(session.messages.len(), 2);

    // User message
    let user_msg = &session.messages[0];
    assert_eq!(user_msg.role, Role::User);
    assert_eq!(user_msg.content, "Hello, can you help me?");
    assert!(user_msg.tool_calls.is_empty());

    // Assistant message with tool calls
    let asst_msg = &session.messages[1];
    assert_eq!(asst_msg.role, Role::Assistant);
    assert_eq!(asst_msg.content, "Of course! How can I help?");
    assert_eq!(asst_msg.tokens, Some(150));
    assert_eq!(
        asst_msg.thinking_trace.as_deref(),
        Some("Let me read the file first.")
    );

    // Tool call
    assert_eq!(asst_msg.tool_calls.len(), 1);
    let tc = &asst_msg.tool_calls[0];
    assert_eq!(tc.id, "tc_001");
    assert_eq!(tc.name, "read_file");
    assert!(tc.approved);
    assert_eq!(tc.result_summary.as_deref(), Some("Read 1 line"));
}

#[test]
fn test_python_session_file_changes() {
    let session: Session = serde_json::from_str(PYTHON_SESSION_JSON).unwrap();

    assert_eq!(session.file_changes.len(), 1);
    let fc = &session.file_changes[0];
    assert_eq!(fc.change_type, FileChangeType::Modified);
    assert_eq!(fc.file_path, "src/main.py");
    assert_eq!(fc.lines_added, 5);
    assert_eq!(fc.lines_removed, 2);
}

#[test]
fn test_python_session_metadata() {
    let session: Session = serde_json::from_str(PYTHON_SESSION_JSON).unwrap();

    let meta = session.get_metadata();
    assert_eq!(meta.title.as_deref(), Some("Test Session"));
    assert_eq!(meta.summary.as_deref(), Some("A test"));
    assert_eq!(meta.tags, vec!["test"]);
    assert_eq!(meta.message_count, 2);
    assert_eq!(meta.summary_files, 1);
    assert_eq!(meta.summary_additions, 5);
    assert_eq!(meta.summary_deletions, 2);
}

#[test]
fn test_python_session_roundtrip() {
    let session: Session = serde_json::from_str(PYTHON_SESSION_JSON).unwrap();

    // Serialize back to JSON
    let rust_json = serde_json::to_string_pretty(&session).unwrap();

    // Deserialize again
    let session2: Session = serde_json::from_str(&rust_json).unwrap();

    assert_eq!(session.id, session2.id);
    assert_eq!(session.messages.len(), session2.messages.len());
    assert_eq!(session.channel, session2.channel);
    assert_eq!(session.file_changes.len(), session2.file_changes.len());
}
