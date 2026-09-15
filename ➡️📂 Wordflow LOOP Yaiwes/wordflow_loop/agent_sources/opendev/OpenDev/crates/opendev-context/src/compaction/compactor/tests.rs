use super::super::tests::{make_assistant_with_tc, make_msg, make_tool_msg};
use super::super::{PROTECTED_TOOL_TYPES, SLIDING_WINDOW_RECENT, SLIDING_WINDOW_THRESHOLD};
use super::*;

#[test]
fn test_optimization_levels() {
    let mut compactor = ContextCompactor::new(1000);

    // At 0% usage
    let messages = vec![make_msg("user", "hi")];
    assert_eq!(
        compactor.check_usage(&messages, ""),
        OptimizationLevel::None
    );

    // Force usage to 75% via API calibration
    compactor.update_from_api_usage(750, 1);
    assert_eq!(
        compactor.check_usage(&messages, ""),
        OptimizationLevel::Warning
    );

    // 85%
    compactor.update_from_api_usage(850, 1);
    assert_eq!(
        compactor.check_usage(&messages, ""),
        OptimizationLevel::Prune
    );

    // 95%
    compactor.update_from_api_usage(950, 1);
    assert_eq!(
        compactor.check_usage(&messages, ""),
        OptimizationLevel::Aggressive
    );

    // 99.5%
    compactor.update_from_api_usage(995, 1);
    assert_eq!(
        compactor.check_usage(&messages, ""),
        OptimizationLevel::Compact
    );
}

#[test]
fn test_should_compact() {
    let mut compactor = ContextCompactor::new(1000);
    let messages = vec![make_msg("user", "hi")];
    assert!(!compactor.should_compact(&messages, ""));

    compactor.update_from_api_usage(995, 1);
    assert!(compactor.should_compact(&messages, ""));
}

#[test]
fn test_mask_old_observations() {
    let compactor = ContextCompactor::new(100_000);

    // Create messages: assistant with tool calls, then 8 tool results
    let mut messages = vec![make_msg("system", "system prompt")];
    let tc_ids: Vec<String> = (0..8).map(|i| format!("tc-{i}")).collect();
    let tc_pairs: Vec<(&str, &str)> = tc_ids.iter().map(|id| (id.as_str(), "bash")).collect();
    messages.push(make_assistant_with_tc(tc_pairs));
    for id in &tc_ids {
        messages.push(make_tool_msg(id, &"x".repeat(100)));
    }

    // Mask level: keep recent 6, mask 2
    compactor.mask_old_observations(&mut messages, OptimizationLevel::Mask);

    let masked: Vec<_> = messages
        .iter()
        .filter(|m| {
            m.get("content")
                .and_then(|v| v.as_str())
                .map(|s| s.starts_with("[ref:"))
                .unwrap_or(false)
        })
        .collect();
    assert_eq!(masked.len(), 2);
}

#[test]
fn test_protected_tools_not_masked() {
    let compactor = ContextCompactor::new(100_000);

    let mut messages = vec![make_msg("system", "sys")];
    let tc_ids: Vec<String> = (0..10).map(|i| format!("tc-{i}")).collect();
    let mut names = vec!["read_file"];
    for _ in 1..10 {
        names.push("bash");
    }
    let pairs: Vec<(&str, &str)> = tc_ids
        .iter()
        .zip(names.iter())
        .map(|(id, name)| (id.as_str(), *name))
        .collect();
    messages.push(make_assistant_with_tc(pairs));
    for id in &tc_ids {
        messages.push(make_tool_msg(id, &"x".repeat(100)));
    }

    compactor.mask_old_observations(&mut messages, OptimizationLevel::Aggressive);

    // tc-0 is read_file and should NOT be masked
    let tc0_msg = messages
        .iter()
        .find(|m| m.get("tool_call_id").and_then(|v| v.as_str()) == Some("tc-0"))
        .unwrap();
    let content = tc0_msg.get("content").and_then(|v| v.as_str()).unwrap();
    assert!(!content.starts_with("[ref:"));
}

#[test]
fn test_compact_small_conversation() {
    let mut compactor = ContextCompactor::new(100_000);
    let messages = vec![
        make_msg("system", "sys"),
        make_msg("user", "hello"),
        make_msg("assistant", "hi"),
    ];
    // Should not compact if <= 4 messages
    let result = compactor.compact(messages.clone(), "sys");
    assert_eq!(result.len(), 3);
}

#[test]
fn test_compact_large_conversation() {
    let mut compactor = ContextCompactor::new(100_000);
    let mut messages = vec![make_msg("system", "sys")];
    for i in 0..20 {
        messages.push(make_msg("user", &format!("question {i}")));
        messages.push(make_msg("assistant", &format!("answer {i}")));
    }
    let original_len = messages.len();
    let result = compactor.compact(messages, "sys");
    assert!(result.len() < original_len);
    // First message preserved
    assert_eq!(
        result[0].get("role").and_then(|v| v.as_str()),
        Some("system")
    );
    // Summary message present
    let has_summary = result.iter().any(|m| {
        m.get("content")
            .and_then(|v| v.as_str())
            .map(|s| s.contains("[CONVERSATION SUMMARY]"))
            .unwrap_or(false)
    });
    assert!(has_summary);
}

#[test]
fn test_compactor_save_load_artifact_index() {
    let mut compactor = ContextCompactor::new(100_000);
    compactor
        .artifact_index
        .record("src/app.rs", "created", "new file");
    compactor
        .artifact_index
        .record("src/app.rs", "modified", "added fn");

    // Save to metadata
    let mut metadata = std::collections::HashMap::new();
    compactor.save_artifact_index(&mut metadata);
    assert!(metadata.contains_key("artifact_index"));

    // Load into a fresh compactor
    let mut compactor2 = ContextCompactor::new(100_000);
    assert!(compactor2.artifact_index.is_empty());
    compactor2.load_artifact_index(&metadata);
    assert_eq!(compactor2.artifact_index.len(), 1);
    let entry = compactor2.artifact_index.entries.get("src/app.rs").unwrap();
    assert_eq!(entry.operation_count, 2);
}

#[test]
fn test_prune_old_tool_outputs() {
    let compactor = ContextCompactor::new(100_000);

    let mut messages = vec![make_msg("system", "sys")];
    // Many tool calls with large outputs
    let tc_ids: Vec<String> = (0..20).map(|i| format!("tc-{i}")).collect();
    let pairs: Vec<(&str, &str)> = tc_ids.iter().map(|id| (id.as_str(), "bash")).collect();
    messages.push(make_assistant_with_tc(pairs));
    for id in &tc_ids {
        // Each tool output is large enough to exceed budget
        messages.push(make_tool_msg(id, &"x".repeat(20_000)));
    }

    compactor.prune_old_tool_outputs(&mut messages);

    let pruned_count = messages
        .iter()
        .filter(|m| m.get("content").and_then(|v| v.as_str()) == Some("[pruned]"))
        .count();
    assert!(pruned_count > 0, "Some messages should have been pruned");
}

#[test]
fn test_fallback_summary() {
    let messages = vec![
        make_msg("user", "What is Rust?"),
        make_msg("assistant", "Rust is a systems programming language."),
        make_msg("user", "Tell me more."),
    ];
    let summary = ContextCompactor::fallback_summary(&messages);
    // Structured format: Goal / Key Actions / Current State
    assert!(summary.contains("## Goal"));
    assert!(summary.contains("What is Rust?"));
    assert!(summary.contains("## Current State"));
    assert!(summary.contains("Rust is a systems programming language."));
}

#[test]
fn test_sliding_window_below_threshold() {
    let mut compactor = ContextCompactor::new(1_000_000);
    let mut messages = vec![make_msg("system", "sys")];
    for i in 0..100 {
        messages.push(make_msg("user", &format!("q{i}")));
        messages.push(make_msg("assistant", &format!("a{i}")));
    }
    // 201 messages, below SLIDING_WINDOW_THRESHOLD (500)
    let result = compactor.sliding_window_compact(messages.clone());
    assert_eq!(result.len(), messages.len());
}

#[test]
fn test_sliding_window_above_threshold() {
    let mut compactor = ContextCompactor::new(1_000_000);
    let mut messages = vec![make_msg("system", "sys")];
    for i in 0..300 {
        messages.push(make_msg("user", &format!("q{i}")));
        messages.push(make_msg("assistant", &format!("a{i}")));
    }
    // 601 messages, above threshold
    assert!(messages.len() >= SLIDING_WINDOW_THRESHOLD);

    let result = compactor.sliding_window_compact(messages.clone());
    // Should keep: 1 (system) + 1 (summary) + SLIDING_WINDOW_RECENT
    assert_eq!(result.len(), 1 + 1 + SLIDING_WINDOW_RECENT);

    // First message is system
    assert_eq!(
        result[0].get("role").and_then(|v| v.as_str()),
        Some("system")
    );
    // Second message is the sliding window summary
    let summary_content = result[1].get("content").and_then(|v| v.as_str()).unwrap();
    assert!(summary_content.contains("[SLIDING WINDOW SUMMARY"));
}

#[test]
fn test_summarize_verbose_tool_outputs() {
    let compactor = ContextCompactor::new(100_000);

    let mut messages = vec![make_msg("system", "sys")];
    let tc_ids: Vec<String> = (0..5).map(|i| format!("tc-{i}")).collect();
    let pairs: Vec<(&str, &str)> = tc_ids.iter().map(|id| (id.as_str(), "bash")).collect();
    messages.push(make_assistant_with_tc(pairs));

    // Mix of short and long outputs
    messages.push(make_tool_msg("tc-0", "ok")); // short, skip
    messages.push(make_tool_msg("tc-1", &"long output line\n".repeat(50))); // > 500
    messages.push(make_tool_msg("tc-2", &"x".repeat(600))); // > 500
    messages.push(make_tool_msg("tc-3", "[pruned]")); // already pruned
    messages.push(make_tool_msg("tc-4", &"data ".repeat(200))); // > 500

    compactor.summarize_verbose_tool_outputs(&mut messages);

    // tc-0 should be unchanged (short)
    let tc0 = messages
        .iter()
        .find(|m| m.get("tool_call_id").and_then(|v| v.as_str()) == Some("tc-0"))
        .unwrap();
    assert_eq!(tc0.get("content").and_then(|v| v.as_str()).unwrap(), "ok");

    // tc-1 should be summarized
    let tc1 = messages
        .iter()
        .find(|m| m.get("tool_call_id").and_then(|v| v.as_str()) == Some("tc-1"))
        .unwrap();
    assert!(
        tc1.get("content")
            .and_then(|v| v.as_str())
            .unwrap()
            .starts_with("[summary:")
    );

    // tc-3 should remain [pruned]
    let tc3 = messages
        .iter()
        .find(|m| m.get("tool_call_id").and_then(|v| v.as_str()) == Some("tc-3"))
        .unwrap();
    assert_eq!(
        tc3.get("content").and_then(|v| v.as_str()).unwrap(),
        "[pruned]"
    );
}

#[test]
fn test_summarize_skips_protected_tools() {
    let compactor = ContextCompactor::new(100_000);

    let mut messages = vec![make_msg("system", "sys")];
    let pairs = vec![("tc-0", "read_file"), ("tc-1", "bash")];
    messages.push(make_assistant_with_tc(pairs));
    messages.push(make_tool_msg("tc-0", &"file content ".repeat(100))); // protected
    messages.push(make_tool_msg("tc-1", &"bash output ".repeat(100))); // not protected

    compactor.summarize_verbose_tool_outputs(&mut messages);

    // read_file output should NOT be summarized
    let tc0 = messages
        .iter()
        .find(|m| m.get("tool_call_id").and_then(|v| v.as_str()) == Some("tc-0"))
        .unwrap();
    assert!(
        !tc0.get("content")
            .and_then(|v| v.as_str())
            .unwrap()
            .starts_with("[summary:")
    );

    // bash output SHOULD be summarized
    let tc1 = messages
        .iter()
        .find(|m| m.get("tool_call_id").and_then(|v| v.as_str()) == Some("tc-1"))
        .unwrap();
    assert!(
        tc1.get("content")
            .and_then(|v| v.as_str())
            .unwrap()
            .starts_with("[summary:")
    );
}

#[test]
fn test_count_message_tokens_integration() {
    let messages = vec![
        make_msg("system", "You are a helpful assistant."),
        make_msg("user", "Hello world"),
        make_msg("assistant", "Hi there! How can I help?"),
    ];
    let total = ContextCompactor::count_message_tokens(&messages, "system prompt");
    assert!(total > 0);
}

#[test]
fn test_prune_skips_summarized_outputs() {
    let compactor = ContextCompactor::new(100_000);

    let mut messages = vec![make_msg("system", "sys")];
    let tc_ids: Vec<String> = (0..5).map(|i| format!("tc-{i}")).collect();
    let pairs: Vec<(&str, &str)> = tc_ids.iter().map(|id| (id.as_str(), "bash")).collect();
    messages.push(make_assistant_with_tc(pairs));

    // Some already summarized, some not
    messages.push(make_tool_msg(
        "tc-0",
        "[summary: bash succeeded, 10 lines]\nfirst line",
    ));
    messages.push(make_tool_msg("tc-1", &"x".repeat(20_000)));
    messages.push(make_tool_msg("tc-2", &"y".repeat(20_000)));
    messages.push(make_tool_msg(
        "tc-3",
        "[summary: bash failed, 5 lines]\nerror",
    ));
    messages.push(make_tool_msg("tc-4", &"z".repeat(20_000)));

    compactor.prune_old_tool_outputs(&mut messages);

    // Summarized messages should NOT be changed to [pruned]
    let tc0 = messages
        .iter()
        .find(|m| m.get("tool_call_id").and_then(|v| v.as_str()) == Some("tc-0"))
        .unwrap();
    assert!(
        tc0.get("content")
            .and_then(|v| v.as_str())
            .unwrap()
            .starts_with("[summary:")
    );
}

#[test]
fn test_sanitize_for_summarization() {
    let messages = vec![
        make_msg("user", "Fix the login bug"),
        make_msg("assistant", "I'll look into that"),
        make_msg("tool", ""), // empty content, should be skipped
    ];
    let sanitized = ContextCompactor::sanitize_for_summarization(&messages);
    assert!(sanitized.contains("[user]"));
    assert!(sanitized.contains("[assistant]"));
    assert!(!sanitized.contains("[tool]"));
}

#[test]
fn test_sanitize_truncates_long_content() {
    let long_content = "x".repeat(1000);
    let messages = vec![make_msg("user", &long_content)];
    let sanitized = ContextCompactor::sanitize_for_summarization(&messages);
    // [user] prefix + space + 500 chars of content
    assert!(sanitized.len() < 520);
}

#[test]
fn test_build_compaction_payload() {
    let compactor = ContextCompactor::new(100_000);
    let messages = vec![
        make_msg("system", "You are helpful."),
        make_msg("user", "Step 1"),
        make_msg("assistant", "Done step 1"),
        make_msg("user", "Step 2"),
        make_msg("assistant", "Done step 2"),
        make_msg("user", "Step 3"),
        make_msg("assistant", "Done step 3"),
    ];

    let result = compactor.build_compaction_payload(&messages, "Summarize.", "gpt-4o-mini");
    assert!(result.is_some());

    let (payload, middle_count, keep_recent) = result.unwrap();
    assert!(middle_count > 0);
    assert!(keep_recent >= 2);
    assert_eq!(
        payload.pointer("/messages/0/role").and_then(|v| v.as_str()),
        Some("system")
    );
    assert_eq!(
        payload.get("model").and_then(|v| v.as_str()),
        Some("gpt-4o-mini")
    );
}

#[test]
fn test_build_compaction_payload_too_few() {
    let compactor = ContextCompactor::new(100_000);
    let messages = vec![make_msg("system", "sys"), make_msg("user", "hi")];
    assert!(
        compactor
            .build_compaction_payload(&messages, "sys", "model")
            .is_none()
    );
}

#[test]
fn test_apply_llm_compaction() {
    let mut compactor = ContextCompactor::new(100_000);
    let messages = vec![
        make_msg("system", "You are helpful."),
        make_msg("user", "Step 1"),
        make_msg("assistant", "Done step 1"),
        make_msg("user", "Step 2"),
        make_msg("assistant", "Done step 2"),
        make_msg("user", "Step 3"),
        make_msg("assistant", "Done step 3"),
    ];

    let keep_recent = 2;
    let result = compactor.apply_llm_compaction(
        messages,
        "This is the LLM summary of the conversation.",
        keep_recent,
    );

    // head(1) + summary(1) + tail(keep_recent)
    assert_eq!(result.len(), 1 + 1 + keep_recent);
    assert_eq!(
        result[0].get("role").and_then(|v| v.as_str()),
        Some("system")
    );
    let summary = result[1].get("content").and_then(|v| v.as_str()).unwrap();
    assert!(summary.contains("[CONVERSATION SUMMARY]"));
    assert!(summary.contains("LLM summary"));
}

#[test]
fn test_apply_llm_compaction_resets_calibration() {
    let mut compactor = ContextCompactor::new(100_000);
    compactor.api_prompt_tokens = 50_000;
    compactor.warned_70 = true;
    compactor.warned_80 = true;

    let messages = vec![
        make_msg("system", "sys"),
        make_msg("user", "a"),
        make_msg("assistant", "b"),
        make_msg("user", "c"),
        make_msg("assistant", "d"),
        make_msg("user", "e"),
    ];

    compactor.apply_llm_compaction(messages, "summary", 2);

    assert_eq!(compactor.api_prompt_tokens, 0);
    assert!(!compactor.warned_70);
    assert!(!compactor.warned_80);
}

#[test]
fn test_prune_skips_small_outputs() {
    let compactor = ContextCompactor::new(100_000);

    let mut messages = vec![make_msg("system", "sys")];
    let tc_ids: Vec<String> = (0..5).map(|i| format!("tc-{i}")).collect();
    let pairs: Vec<(&str, &str)> = tc_ids.iter().map(|id| (id.as_str(), "bash")).collect();
    messages.push(make_assistant_with_tc(pairs));

    // Small output (< PRUNE_MIN_LENGTH)
    messages.push(make_tool_msg("tc-0", "ok"));
    messages.push(make_tool_msg("tc-1", "short result"));
    // Large outputs that should be prunable
    messages.push(make_tool_msg("tc-2", &"x".repeat(20_000)));
    messages.push(make_tool_msg("tc-3", &"y".repeat(20_000)));
    messages.push(make_tool_msg("tc-4", &"z".repeat(20_000)));

    compactor.prune_old_tool_outputs(&mut messages);

    // Small outputs should NOT be pruned
    let tc0 = messages
        .iter()
        .find(|m| m.get("tool_call_id").and_then(|v| v.as_str()) == Some("tc-0"))
        .unwrap();
    assert_eq!(tc0.get("content").and_then(|v| v.as_str()).unwrap(), "ok");

    let tc1 = messages
        .iter()
        .find(|m| m.get("tool_call_id").and_then(|v| v.as_str()) == Some("tc-1"))
        .unwrap();
    assert_eq!(
        tc1.get("content").and_then(|v| v.as_str()).unwrap(),
        "short result"
    );
}

#[test]
fn test_protected_tool_types_includes_web_screenshot() {
    assert!(PROTECTED_TOOL_TYPES.contains(&"web_screenshot"));
    assert!(PROTECTED_TOOL_TYPES.contains(&"vlm"));
}

#[test]
fn test_set_max_context() {
    let mut compactor = ContextCompactor::new(100_000);
    compactor.update_from_api_usage(50_000, 10);
    assert!((compactor.usage_pct() - 50.0).abs() < 0.1);

    // Switching to a model with larger context window
    compactor.set_max_context(400_000);
    assert!((compactor.usage_pct() - 12.5).abs() < 0.1);
}

#[test]
fn test_invalidate_calibration_forces_recount() {
    let mut compactor = ContextCompactor::new(100_000);

    // Calibrate with API usage
    compactor.update_from_api_usage(80_000, 5);
    assert_eq!(compactor.api_prompt_tokens, 80_000);
    assert_eq!(compactor.msg_count_at_calibration, 5);

    // Invalidate (simulating staged compaction that reduced content)
    compactor.invalidate_calibration();
    assert_eq!(compactor.api_prompt_tokens, 0);
    assert_eq!(compactor.msg_count_at_calibration, 0);

    // Next check_usage should recount from actual messages (fallback path)
    let messages = vec![make_msg("user", "short"), make_msg("assistant", "reply")];
    let level = compactor.check_usage(&messages, "sys");
    // With small messages, usage should be far below any threshold
    assert_eq!(level, OptimizationLevel::None);
    assert!(compactor.usage_pct() < 1.0);
}

/// Simulate a realistic conversation with a small context window (10,000 tokens)
/// to verify that compaction thresholds fire at the right levels and that
/// usage_pct is accurate after calibration.
#[test]
fn test_simulated_conversation_small_context() {
    let max_context: u64 = 10_000;
    let mut compactor = ContextCompactor::new(max_context);

    // Turn 1: API reports 2,000 total tokens (input + output)
    compactor.update_from_api_usage(2_000, 3);
    assert!((compactor.usage_pct() - 20.0).abs() < 0.1);
    assert_eq!(
        compactor.check_usage(&[make_msg("user", "hi")], ""),
        OptimizationLevel::None
    );

    // Turn 2: conversation grows to 5,500 tokens
    compactor.update_from_api_usage(5_500, 8);
    assert!((compactor.usage_pct() - 55.0).abs() < 0.1);
    assert_eq!(
        compactor.check_usage(&[make_msg("user", "hi")], ""),
        OptimizationLevel::None
    );

    // Turn 3: hits 72% — warning threshold
    compactor.update_from_api_usage(7_200, 12);
    assert!((compactor.usage_pct() - 72.0).abs() < 0.1);
    let messages: Vec<_> = (0..12)
        .map(|i| make_msg("user", &format!("msg {i}")))
        .collect();
    assert_eq!(
        compactor.check_usage(&messages, ""),
        OptimizationLevel::Warning
    );

    // Turn 4: hits 82% — mask threshold
    compactor.update_from_api_usage(8_200, 15);
    let messages: Vec<_> = (0..15)
        .map(|i| make_msg("user", &format!("msg {i}")))
        .collect();
    assert_eq!(
        compactor.check_usage(&messages, ""),
        OptimizationLevel::Mask
    );

    // Turn 5: hits 92% — aggressive threshold
    compactor.update_from_api_usage(9_200, 18);
    let messages: Vec<_> = (0..18)
        .map(|i| make_msg("user", &format!("msg {i}")))
        .collect();
    assert_eq!(
        compactor.check_usage(&messages, ""),
        OptimizationLevel::Aggressive
    );

    // Simulate staged compaction: content is masked, calibration invalidated
    compactor.invalidate_calibration();
    // Recount from actual (small) messages — should show much lower usage
    let small_messages: Vec<_> = (0..18)
        .map(|i| make_msg("user", &format!("m{i}")))
        .collect();
    let level = compactor.check_usage(&small_messages, "sys");
    // Recounted from tiny messages — usage should be well under 70%
    assert!(
        compactor.usage_pct() < 70.0,
        "After invalidation, usage should recount from actual messages"
    );
    assert!(matches!(
        level,
        OptimizationLevel::None | OptimizationLevel::Warning
    ));
}

/// Verify that with the correct model context_length (e.g. 400k for GPT-5.2),
/// a conversation at 93k tokens does NOT trigger compaction.
#[test]
fn test_no_premature_compaction_with_correct_context_length() {
    // Before fix: max_context defaulted to 100k, 93k tokens = 93% → Aggressive
    let mut compactor_wrong = ContextCompactor::new(100_000);
    compactor_wrong.update_from_api_usage(93_224, 39);
    let msgs: Vec<_> = (0..39)
        .map(|i| make_msg("user", &format!("msg {i}")))
        .collect();
    assert_eq!(
        compactor_wrong.check_usage(&msgs, ""),
        OptimizationLevel::Aggressive
    );

    // After fix: max_context = 400k (GPT-5.2 actual), 93k tokens = 23.3% → None
    let mut compactor_fixed = ContextCompactor::new(400_000);
    compactor_fixed.update_from_api_usage(93_224, 39);
    let msgs: Vec<_> = (0..39)
        .map(|i| make_msg("user", &format!("msg {i}")))
        .collect();
    assert_eq!(
        compactor_fixed.check_usage(&msgs, ""),
        OptimizationLevel::None
    );
    assert!((compactor_fixed.usage_pct() - 23.3).abs() < 0.1);
}

/// Simulate set_max_context being called mid-conversation (model switch).
#[test]
fn test_model_switch_updates_context_percentage() {
    let mut compactor = ContextCompactor::new(100_000);
    compactor.update_from_api_usage(80_000, 20);
    // 80% used with old model
    assert!((compactor.usage_pct() - 80.0).abs() < 0.1);

    // Switch to model with 200k context
    compactor.set_max_context(200_000);
    // Same tokens, bigger window → 40%
    assert!((compactor.usage_pct() - 40.0).abs() < 0.1);

    // Compaction check should reflect new limit
    let msgs: Vec<_> = (0..20)
        .map(|i| make_msg("user", &format!("msg {i}")))
        .collect();
    assert_eq!(compactor.check_usage(&msgs, ""), OptimizationLevel::None);
}

/// Verify update_from_api_usage now accepts total tokens (input + output).
#[test]
fn test_total_tokens_calibration() {
    let mut compactor = ContextCompactor::new(200_000);

    // Simulate: input=80k, output=20k → total=100k
    let input_tokens: u64 = 80_000;
    let output_tokens: u64 = 20_000;
    compactor.update_from_api_usage(input_tokens + output_tokens, 15);

    // 100k / 200k = 50%
    assert!((compactor.usage_pct() - 50.0).abs() < 0.1);
}
