use super::*;
use crate::event::AppEvent;

#[test]
fn test_app_creation() {
    let app = App::new();
    assert!(app.state.running);
    assert_eq!(app.state.mode, OperationMode::Normal);
}

#[test]
fn test_should_render_before_draining_on_live_subagent_events() {
    assert!(App::should_render_before_draining(
        &AppEvent::ReasoningContent("thinking".into(),)
    ));
    assert!(App::should_render_before_draining(&AppEvent::ToolStarted {
        tool_id: "t1".into(),
        tool_name: "spawn_subagent".into(),
        args: std::collections::HashMap::new(),
    }));
    assert!(App::should_render_before_draining(
        &AppEvent::SubagentStarted {
            subagent_id: "sa1".into(),
            subagent_name: "Explore".into(),
            task: "Inspect auth".into(),
            cancel_token: None,
        }
    ));
    assert!(App::should_render_before_draining(
        &AppEvent::ToolFinished {
            tool_id: "t1".into(),
            success: true,
        }
    ));
}

#[test]
fn test_should_not_force_render_before_draining_on_tick() {
    assert!(!App::should_render_before_draining(&AppEvent::Tick));
}

// ---------------------------------------------------------------
// Shared input-area height helper (issue #61)
// ---------------------------------------------------------------

#[test]
fn test_input_area_height_empty_buffer() {
    let app = App::new();
    assert_eq!(app.input_area_height(80), 2); // 1 text row + separator
}

#[test]
fn test_input_area_height_explicit_newlines() {
    let mut app = App::new();
    app.state.input_buffer = "a\nb\nc".to_string();
    assert_eq!(app.input_area_height(80), 4); // 3 rows + separator
}

#[test]
fn test_input_area_height_soft_wrapped_long_line() {
    let mut app = App::new();
    // width 80 → content 78; 200 chars → 3 wrapped rows + separator
    app.state.input_buffer = "a".repeat(200);
    assert_eq!(app.input_area_height(80), 4);
}

#[test]
fn test_input_area_height_capped_at_8() {
    let mut app = App::new();
    app.state.input_buffer = "x\n".repeat(20);
    assert_eq!(app.input_area_height(80), 8);
    app.state.input_buffer = "a".repeat(2000); // 26 wrapped rows at width 80
    assert_eq!(app.input_area_height(80), 8);
}

#[test]
fn test_input_area_height_degenerate_width() {
    let mut app = App::new();
    app.state.input_buffer = "a".repeat(500);
    // Width ≤ prefix → wrapping disabled → 1 logical row + separator
    assert_eq!(app.input_area_height(0), 2);
}
