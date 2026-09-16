use super::*;

#[test]
fn test_input_widget_creation() {
    let _widget = InputWidget::new("hello", 3, "NORMAL", 0, 0, None);
}

#[test]
fn test_input_widget_empty() {
    let _widget = InputWidget::new("", 0, "NORMAL", 0, 0, None);
}

#[test]
fn test_queue_indicator_in_separator() {
    // Verify the widget renders queue count in the separator line (row 0)
    let area = Rect::new(0, 0, 60, 3);
    let mut buf = Buffer::empty(area);

    let widget = InputWidget::new("", 0, "NORMAL", 2, 0, None);
    widget.render(area, &mut buf);

    let rendered: String = (0..area.width)
        .map(|x| {
            buf.cell((x, 0))
                .map_or(' ', |c| c.symbol().chars().next().unwrap_or(' '))
        })
        .collect();
    assert!(
        rendered.contains("2 messages queued"),
        "Expected '2 messages queued' in separator line, got: {rendered:?}"
    );
}

#[test]
fn test_queue_indicator_single_message() {
    let area = Rect::new(0, 0, 60, 3);
    let mut buf = Buffer::empty(area);

    let widget = InputWidget::new("", 0, "NORMAL", 1, 0, None);
    widget.render(area, &mut buf);

    let rendered: String = (0..area.width)
        .map(|x| {
            buf.cell((x, 0))
                .map_or(' ', |c| c.symbol().chars().next().unwrap_or(' '))
        })
        .collect();
    assert!(
        rendered.contains("1 message queued"),
        "Expected '1 message queued' in separator line, got: {rendered:?}"
    );
    assert!(
        !rendered.contains("1 messages"),
        "Should use singular 'message' for count=1"
    );
}

#[test]
fn test_queue_indicator_bg_results_only() {
    let area = Rect::new(0, 0, 60, 3);
    let mut buf = Buffer::empty(area);

    let widget = InputWidget::new("", 0, "NORMAL", 0, 2, None);
    widget.render(area, &mut buf);

    let rendered: String = (0..area.width)
        .map(|x| {
            buf.cell((x, 0))
                .map_or(' ', |c| c.symbol().chars().next().unwrap_or(' '))
        })
        .collect();
    assert!(
        rendered.contains("2 results queued"),
        "Expected '2 results queued' in separator line, got: {rendered:?}"
    );
    // No ESC hint for bg-only results
    assert!(
        !rendered.contains("ESC"),
        "Should not show ESC hint for bg-only results, got: {rendered:?}"
    );
}

#[test]
fn test_queue_indicator_mixed() {
    let area = Rect::new(0, 0, 60, 3);
    let mut buf = Buffer::empty(area);

    let widget = InputWidget::new("", 0, "NORMAL", 1, 2, None);
    widget.render(area, &mut buf);

    let rendered: String = (0..area.width)
        .map(|x| {
            buf.cell((x, 0))
                .map_or(' ', |c| c.symbol().chars().next().unwrap_or(' '))
        })
        .collect();
    assert!(
        rendered.contains("3 queued"),
        "Expected '3 queued' in separator line, got: {rendered:?}"
    );
}

#[test]
fn test_activity_tag_renders() {
    let area = Rect::new(0, 0, 80, 3);
    let mut buf = Buffer::empty(area);

    let widget = InputWidget::new("", 0, "NORMAL", 0, 0, Some("implementing status bar"));
    widget.render(area, &mut buf);

    let rendered: String = (0..area.width)
        .map(|x| {
            buf.cell((x, 0))
                .map_or(' ', |c| c.symbol().chars().next().unwrap_or(' '))
        })
        .collect();
    assert!(
        rendered.contains("implementing-status-bar"),
        "Expected kebab-cased activity tag in separator line, got: {rendered:?}"
    );
}

#[test]
fn test_activity_tag_with_queue() {
    let area = Rect::new(0, 0, 100, 3);
    let mut buf = Buffer::empty(area);

    let widget = InputWidget::new("", 0, "NORMAL", 1, 0, Some("debugging login"));
    widget.render(area, &mut buf);

    let rendered: String = (0..area.width)
        .map(|x| {
            buf.cell((x, 0))
                .map_or(' ', |c| c.symbol().chars().next().unwrap_or(' '))
        })
        .collect();
    assert!(
        rendered.contains("1 message queued"),
        "Expected queue indicator, got: {rendered:?}"
    );
    assert!(
        rendered.contains("debugging-login"),
        "Expected kebab-cased activity tag, got: {rendered:?}"
    );
}

#[test]
fn test_to_kebab_display() {
    assert_eq!(to_kebab_display("Hello World"), "hello-world");
    assert_eq!(to_kebab_display("Auth Refactor"), "auth-refactor");
    assert_eq!(to_kebab_display("Fix: login bug!"), "fix-login-bug");
    assert_eq!(to_kebab_display("  spaces  "), "spaces");
    assert_eq!(to_kebab_display("already-kebab"), "already-kebab");
    assert_eq!(to_kebab_display("MiXeD CaSe"), "mixed-case");
}

#[test]
fn test_to_kebab_display_long_title_no_truncation() {
    let long_title = "implementing the new authentication middleware refactor";
    let kebab = to_kebab_display(long_title);
    assert_eq!(
        kebab,
        "implementing-the-new-authentication-middleware-refactor"
    );
    // No truncation — full string preserved
    assert!(!kebab.contains("..."));
    assert!(kebab.len() > 30);
}

// ---------------------------------------------------------------
// Soft-wrap engine: wrap_line / input_visual_rows
// ---------------------------------------------------------------

#[test]
fn test_wrap_line_empty() {
    assert_eq!(wrap_line("", 10), [0..0]);
}

#[test]
fn test_wrap_line_short() {
    assert_eq!(wrap_line("hello", 10), [0..5]);
}

#[test]
fn test_wrap_line_exactly_at_width_adds_cursor_row() {
    // Exactly-full row gains a trailing empty row for the end-of-line cursor
    assert_eq!(wrap_line("hello", 5), [0..5, 5..5]);
}

#[test]
fn test_wrap_line_long_ascii() {
    let line = "a".repeat(12);
    assert_eq!(wrap_line(&line, 5), [0..5, 5..10, 10..12]);
}

#[test]
fn test_wrap_line_exact_multiple() {
    let line = "a".repeat(10);
    assert_eq!(wrap_line(&line, 5), [0..5, 5..10, 10..10]);
}

#[test]
fn test_wrap_line_cjk_display_width() {
    // Each CJK char: 2 display cols, 3 bytes. Width 5 fits two chars per row.
    assert_eq!(wrap_line("你好世界", 5), [0..6, 6..12]);
}

#[test]
fn test_wrap_line_wide_char_narrower_than_width() {
    // A char wider than the row still occupies one row (no infinite loop)
    assert_eq!(wrap_line("你", 1), [0..3, 3..3]);
}

#[test]
fn test_wrap_line_zero_width_disables_wrapping() {
    assert_eq!(wrap_line("abcdef", 0), [0..6]);
}

#[test]
fn test_input_visual_rows_empty_buffer() {
    assert_eq!(input_visual_rows("", 80), 1);
}

#[test]
fn test_input_visual_rows_newlines_only() {
    assert_eq!(input_visual_rows("a\nb\nc", 80), 3);
    assert_eq!(input_visual_rows("\n\n", 80), 3);
}

#[test]
fn test_input_visual_rows_long_line_wraps() {
    // width 80 → content 78: 200 = 78 + 78 + 44 → 3 rows
    let buffer = "a".repeat(200);
    assert_eq!(input_visual_rows(&buffer, 80), 3);
}

#[test]
fn test_input_visual_rows_exact_multiple_of_width() {
    // 156 = 2 * 78 → two full rows + trailing cursor row
    let buffer = "a".repeat(156);
    assert_eq!(input_visual_rows(&buffer, 80), 3);
}

#[test]
fn test_input_visual_rows_mixed_newlines_and_wrapping() {
    let buffer = format!("{}\nshort", "a".repeat(100)); // 100 = 78 + 22 → 2 rows, +1
    assert_eq!(input_visual_rows(&buffer, 80), 3);
}

#[test]
fn test_input_visual_rows_degenerate_width() {
    // Width ≤ prefix width → content width 0 → one row per logical line
    assert_eq!(input_visual_rows("aaaa\nbb", 0), 2);
    assert_eq!(input_visual_rows("aaaa\nbb", 2), 2);
}

// ---------------------------------------------------------------
// Render: wrapping, cursor mapping, scroll-into-view
// ---------------------------------------------------------------

fn row_text(buf: &Buffer, area: Rect, y: u16) -> String {
    (0..area.width)
        .map(|x| {
            buf.cell((x, y))
                .map_or(' ', |c| c.symbol().chars().next().unwrap_or(' '))
        })
        .collect()
}

/// Locate the reverse-video cursor cell (white background) in the buffer.
fn cursor_cell(buf: &Buffer, area: Rect) -> Option<(u16, u16)> {
    for y in 0..area.height {
        for x in 0..area.width {
            if buf
                .cell((x, y))
                .is_some_and(|c| c.style().bg == Some(Color::White))
            {
                return Some((x, y));
            }
        }
    }
    None
}

fn render_input(buffer: &str, cursor: usize, area: Rect) -> Buffer {
    let mut buf = Buffer::empty(area);
    InputWidget::new(buffer, cursor, "NORMAL", 0, 0, None).render(area, &mut buf);
    buf
}

#[test]
fn test_render_short_input_unchanged() {
    // No visual regression for input that fits on one row
    let area = Rect::new(0, 0, 60, 3);
    let buf = render_input("hello", 5, area);
    assert!(
        row_text(&buf, area, 1).starts_with("> hello"),
        "got: {:?}",
        row_text(&buf, area, 1)
    );
    // Cursor: virtual cell right after the text (2 prefix + 5 chars)
    assert_eq!(cursor_cell(&buf, area), Some((7, 1)));
}

#[test]
fn test_render_long_line_wraps_across_rows() {
    // width 20 → content 18; 40 chars → rows of 18 + 18 + 4
    let area = Rect::new(0, 0, 20, 5);
    let line = "a".repeat(40);
    let buf = render_input(&line, 0, area);

    let r1 = row_text(&buf, area, 1);
    let r2 = row_text(&buf, area, 2);
    let r3 = row_text(&buf, area, 3);
    assert_eq!(r1, format!("> {}", "a".repeat(18)), "row 1: {r1:?}");
    assert_eq!(r2, format!("  {}", "a".repeat(18)), "row 2: {r2:?}");
    assert_eq!(r3, format!("  {:<18}", "a".repeat(4)), "row 3: {r3:?}");
}

#[test]
fn test_render_cursor_on_first_wrapped_row() {
    let area = Rect::new(0, 0, 20, 5);
    let line = "a".repeat(40);
    let buf = render_input(&line, 5, area);
    // prefix (2) + column 5 on visual row 0
    assert_eq!(cursor_cell(&buf, area), Some((7, 1)));
}

#[test]
fn test_render_cursor_at_wrap_seam() {
    // Cursor at byte 18 = first byte of the second visual row
    let area = Rect::new(0, 0, 20, 5);
    let line = "a".repeat(40);
    let buf = render_input(&line, 18, area);
    assert_eq!(cursor_cell(&buf, area), Some((2, 2)));
}

#[test]
fn test_render_cursor_at_buffer_end_virtual_cell() {
    // Cursor past the last char renders as a virtual cell after the text
    let area = Rect::new(0, 0, 20, 5);
    let line = "a".repeat(40); // last row holds 4 chars
    let buf = render_input(&line, 40, area);
    assert_eq!(cursor_cell(&buf, area), Some((6, 3)));
}

#[test]
fn test_render_cursor_at_end_of_exactly_full_row() {
    // 18 chars exactly fill the first row; end-of-line cursor gets its own row
    let area = Rect::new(0, 0, 20, 5);
    let line = "a".repeat(18);
    let buf = render_input(&line, 18, area);
    assert_eq!(cursor_cell(&buf, area), Some((2, 2)));
}

#[test]
fn test_render_cjk_wraps_by_display_width() {
    // width 12 → content 10 → five 2-col chars per row
    let area = Rect::new(0, 0, 12, 4);
    let text = "你好世界你好世界"; // 8 chars, 16 cols
    let buf = render_input(text, 0, area);

    let r1 = row_text(&buf, area, 1);
    let r2 = row_text(&buf, area, 2);
    assert!(r1.starts_with("> 你"), "row 1: {r1:?}");
    // Second row starts with the 6th char (byte 15)
    assert_eq!(
        buf.cell((2, 2)).map(|c| c.symbol().to_string()),
        Some("好".to_string()),
        "row 2: {r2:?}"
    );
}

#[test]
fn test_render_scrolls_to_keep_cursor_visible() {
    // 10 logical lines, 7 visible text rows → scroll so the last row shows.
    // This also covers the pre-existing bug where >7 explicit newlines
    // silently hid the trailing lines.
    let area = Rect::new(0, 0, 40, 8);
    let buffer = (0..10)
        .map(|i| format!("l{i}"))
        .collect::<Vec<_>>()
        .join("\n");
    let buf = render_input(&buffer, buffer.len(), area);

    // Rows 3..=9 visible: top text row shows l3, bottom shows l9
    assert!(
        row_text(&buf, area, 1).contains("l3"),
        "top: {:?}",
        row_text(&buf, area, 1)
    );
    assert!(
        row_text(&buf, area, 7).contains("l9"),
        "bottom: {:?}",
        row_text(&buf, area, 7)
    );
    assert!(!row_text(&buf, area, 1).contains("l0"));
    // Scrolled view: the "> " prompt row is off-screen
    assert!(row_text(&buf, area, 1).starts_with("  "));
    // Cursor: virtual cell after "l9" on the bottom row
    assert_eq!(cursor_cell(&buf, area), Some((4, 7)));
}

#[test]
fn test_render_no_scroll_when_cursor_at_top() {
    let area = Rect::new(0, 0, 40, 8);
    let buffer = (0..10)
        .map(|i| format!("l{i}"))
        .collect::<Vec<_>>()
        .join("\n");
    let buf = render_input(&buffer, 0, area);

    assert!(row_text(&buf, area, 1).starts_with("> l0"));
    assert!(row_text(&buf, area, 7).contains("l6"));
    assert_eq!(cursor_cell(&buf, area), Some((2, 1)));
}

#[test]
fn test_render_scrolls_wrapped_rows_to_cursor() {
    // A single unbroken line producing more wrapped rows than the cap:
    // width 20 → content 18; 10 * 18 = 180 chars → 10 full rows + cursor row.
    let area = Rect::new(0, 0, 20, 8); // 7 text rows
    let line = "ab".repeat(90); // 180 chars
    let buf = render_input(&line, 180, area);

    // Cursor (end of buffer) on the bottom visible row, start of the
    // trailing empty row
    assert_eq!(cursor_cell(&buf, area), Some((2, 7)));
    // All visible rows are continuations (prompt row scrolled off)
    assert!(row_text(&buf, area, 1).starts_with("  ab"));
}

#[test]
fn test_render_continuation_prefix_matches_indent_constant() {
    let area = Rect::new(0, 0, 20, 5);
    let buf = render_input("first\nsecond", 0, area);
    let r2 = row_text(&buf, area, 2);
    assert!(
        r2.starts_with(&format!("{}second", style_tokens::Indent::CONT)),
        "row 2 should use Indent::CONT prefix, got: {r2:?}"
    );
}

#[test]
fn test_activity_tag_long_title_not_truncated() {
    let area = Rect::new(0, 0, 120, 3);
    let mut buf = Buffer::empty(area);

    let long_tag = "implementing the new authentication middleware refactor";
    let widget = InputWidget::new("", 0, "NORMAL", 0, 0, Some(long_tag));
    widget.render(area, &mut buf);

    let rendered: String = (0..area.width)
        .map(|x| {
            buf.cell((x, 0))
                .map_or(' ', |c| c.symbol().chars().next().unwrap_or(' '))
        })
        .collect();
    // Full kebab tag should appear, no "..." truncation
    assert!(
        rendered.contains("implementing-the-new-authentication-middleware-refactor"),
        "Expected full long tag without truncation, got: {rendered:?}"
    );
    assert!(
        !rendered.contains("..."),
        "Tag should not be truncated, got: {rendered:?}"
    );
}
