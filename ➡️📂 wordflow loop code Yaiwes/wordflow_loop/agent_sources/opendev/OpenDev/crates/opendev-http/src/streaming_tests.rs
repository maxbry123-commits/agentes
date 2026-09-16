use super::*;

#[test]
fn parse_sse_data_accepts_data_without_space() {
    let parsed = parse_sse_data(r#"data:{"type":"chunk"}"#).expect("data line should parse");
    assert_eq!(parsed["type"], "chunk");
}

#[test]
fn is_sse_done_accepts_data_without_space() {
    assert!(is_sse_done("data:[DONE]"));
    assert!(is_sse_done("data: [DONE]"));
}
