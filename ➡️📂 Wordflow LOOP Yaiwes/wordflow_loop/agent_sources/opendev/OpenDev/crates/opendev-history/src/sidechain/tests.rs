use tempfile::TempDir;

use super::*;

fn temp_session_dir() -> TempDir {
    TempDir::new().unwrap()
}

#[test]
fn test_write_and_read_entries() {
    let dir = temp_session_dir();
    let session_dir = dir.path().canonicalize().unwrap();

    let mut writer = SidechainWriter::new(&session_dir, "agent-1").unwrap();
    writer
        .append(EntryKind::SystemPrompt {
            content: "You are a helpful agent.".into(),
        })
        .unwrap();
    writer
        .append(EntryKind::AssistantMsg {
            content: "I'll help you.".into(),
            tool_calls: None,
        })
        .unwrap();
    writer
        .append(EntryKind::ToolResult {
            call_id: "call-1".into(),
            name: "read_file".into(),
            output: "file contents".into(),
            ok: true,
        })
        .unwrap();
    writer
        .append(EntryKind::Tokens { inp: 100, out: 50 })
        .unwrap();

    let reader = SidechainReader::open(&session_dir, "agent-1").unwrap();
    let entries = reader.entries().unwrap();
    assert_eq!(entries.len(), 4);
    assert_eq!(entries[0].seq, 0);
    assert_eq!(entries[1].seq, 1);
    assert!(entries[0].ts > 0);
}

#[test]
fn test_tail_returns_last_n() {
    let dir = temp_session_dir();
    let session_dir = dir.path().canonicalize().unwrap();

    let mut writer = SidechainWriter::new(&session_dir, "agent-1").unwrap();
    for i in 0..10 {
        writer
            .append(EntryKind::AssistantMsg {
                content: format!("msg {i}"),
                tool_calls: None,
            })
            .unwrap();
    }

    let reader = SidechainReader::open(&session_dir, "agent-1").unwrap();
    let tail = reader.tail(3).unwrap();
    assert_eq!(tail.len(), 3);
    assert_eq!(tail[0].seq, 7);
    assert_eq!(tail[2].seq, 9);
}

#[test]
fn test_into_messages_reconstructs_history() {
    let dir = temp_session_dir();
    let session_dir = dir.path().canonicalize().unwrap();

    let mut writer = SidechainWriter::new(&session_dir, "agent-1").unwrap();
    writer
        .append(EntryKind::SystemPrompt {
            content: "system".into(),
        })
        .unwrap();
    writer
        .append(EntryKind::AssistantMsg {
            content: "thinking...".into(),
            tool_calls: Some(vec![serde_json::json!({
                "id": "call-1",
                "type": "function",
                "function": { "name": "read_file", "arguments": "{}" }
            })]),
        })
        .unwrap();
    writer
        .append(EntryKind::ToolResult {
            call_id: "call-1".into(),
            name: "read_file".into(),
            output: "contents".into(),
            ok: true,
        })
        .unwrap();
    writer
        .append(EntryKind::AssistantMsg {
            content: "Here's the result.".into(),
            tool_calls: None,
        })
        .unwrap();
    writer
        .append(EntryKind::Tokens { inp: 200, out: 100 })
        .unwrap();

    let reader = SidechainReader::open(&session_dir, "agent-1").unwrap();
    let messages = reader.into_messages().unwrap();

    // System prompt, tokens, and state changes are excluded
    assert_eq!(messages.len(), 3); // assistant + tool_result + assistant
    assert_eq!(messages[0]["role"], "assistant");
    assert_eq!(messages[1]["role"], "tool");
    assert_eq!(messages[1]["tool_call_id"], "call-1");
    assert_eq!(messages[2]["content"], "Here's the result.");
}

#[test]
fn test_corrupt_line_skipped() {
    let dir = temp_session_dir();
    let session_dir = dir.path().canonicalize().unwrap();

    // Write a valid entry
    let mut writer = SidechainWriter::new(&session_dir, "agent-1").unwrap();
    writer
        .append(EntryKind::AssistantMsg {
            content: "valid".into(),
            tool_calls: None,
        })
        .unwrap();

    // Manually inject a corrupt line
    let path = session_dir.join("agents/agent-1.jsonl");
    let mut file = std::fs::OpenOptions::new()
        .append(true)
        .open(&path)
        .unwrap();
    use std::io::Write;
    writeln!(file, "{{this is not valid json}}").unwrap();

    // Write another valid entry
    let mut writer2 = SidechainWriter::new(&session_dir, "agent-1").unwrap();
    writer2
        .append(EntryKind::AssistantMsg {
            content: "also valid".into(),
            tool_calls: None,
        })
        .unwrap();

    let reader = SidechainReader::open(&session_dir, "agent-1").unwrap();
    let entries = reader.entries().unwrap();
    // 2 valid entries, 1 corrupt skipped
    assert_eq!(entries.len(), 2);
}

#[test]
fn test_empty_file_reads_empty() {
    let dir = temp_session_dir();
    let session_dir = dir.path().canonicalize().unwrap();

    // Create empty file
    let agents_dir = session_dir.join("agents");
    std::fs::create_dir_all(&agents_dir).unwrap();
    std::fs::write(agents_dir.join("agent-1.jsonl"), "").unwrap();

    let reader = SidechainReader::open(&session_dir, "agent-1").unwrap();
    let entries = reader.entries().unwrap();
    assert!(entries.is_empty());
}

#[test]
fn test_writer_creates_directories() {
    let dir = temp_session_dir();
    let session_dir = dir.path().canonicalize().unwrap();
    let deep_dir = session_dir.join("deep").join("nested");

    let writer = SidechainWriter::new(&deep_dir, "agent-1");
    assert!(writer.is_ok());
    assert!(deep_dir.join("agents/agent-1.jsonl").exists());
}

#[test]
fn test_reader_nonexistent_file_error() {
    let dir = temp_session_dir();
    let session_dir = dir.path().canonicalize().unwrap();
    let result = SidechainReader::open(&session_dir, "nonexistent");
    assert!(result.is_err());
}

#[test]
fn test_into_messages_filters_orphaned_tool_calls() {
    let dir = temp_session_dir();
    let session_dir = dir.path().canonicalize().unwrap();

    let mut writer = SidechainWriter::new(&session_dir, "agent-1").unwrap();

    // Assistant with tool call but NO matching result (orphaned)
    writer
        .append(EntryKind::AssistantMsg {
            content: "".into(),
            tool_calls: Some(vec![serde_json::json!({
                "id": "orphan-1",
                "type": "function",
                "function": { "name": "bash", "arguments": "{}" }
            })]),
        })
        .unwrap();

    // Normal assistant message
    writer
        .append(EntryKind::AssistantMsg {
            content: "Hello!".into(),
            tool_calls: None,
        })
        .unwrap();

    let reader = SidechainReader::open(&session_dir, "agent-1").unwrap();
    let messages = reader.into_messages().unwrap();

    // Orphaned tool call with empty content should be filtered
    assert_eq!(messages.len(), 1);
    assert_eq!(messages[0]["content"], "Hello!");
}

#[test]
fn test_write_resume_cycle() {
    let dir = temp_session_dir();
    let session_dir = dir.path().canonicalize().unwrap();

    // Write 5 entries
    let mut writer = SidechainWriter::new(&session_dir, "agent-1").unwrap();
    for i in 0..5 {
        writer
            .append(EntryKind::AssistantMsg {
                content: format!("msg {i}"),
                tool_calls: None,
            })
            .unwrap();
    }
    drop(writer);

    // Read back
    let reader = SidechainReader::open(&session_dir, "agent-1").unwrap();
    assert_eq!(reader.entries().unwrap().len(), 5);

    // Write 3 more (new writer picks up from existing file)
    let mut writer2 = SidechainWriter::new(&session_dir, "agent-1").unwrap();
    for i in 5..8 {
        writer2
            .append(EntryKind::AssistantMsg {
                content: format!("msg {i}"),
                tool_calls: None,
            })
            .unwrap();
    }

    // Read all 8
    let reader2 = SidechainReader::open(&session_dir, "agent-1").unwrap();
    let entries = reader2.entries().unwrap();
    assert_eq!(entries.len(), 8);
    assert_eq!(entries[0].seq, 0);
    assert_eq!(entries[7].seq, 7);
}
