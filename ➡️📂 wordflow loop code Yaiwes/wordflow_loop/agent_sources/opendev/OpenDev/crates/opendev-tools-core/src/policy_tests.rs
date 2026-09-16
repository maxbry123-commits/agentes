use super::*;

#[test]
fn test_resolve_full_profile() {
    let allowed = ToolPolicy::resolve("full", None, None).unwrap();
    assert!(allowed.contains("Read"));
    assert!(allowed.contains("Write"));
    assert!(allowed.contains("Bash"));
    assert!(allowed.contains("TaskStop"));
    assert!(allowed.contains("AskUserQuestion"));
    assert!(allowed.contains("SendMessage"));
    assert!(allowed.contains("schedule"));
}

#[test]
fn test_resolve_minimal_profile() {
    let allowed = ToolPolicy::resolve("minimal", None, None).unwrap();
    assert!(allowed.contains("Read"));
    assert!(allowed.contains("Grep"));
    assert!(allowed.contains("TaskStop")); // always allowed
    assert!(!allowed.contains("Write"));
    assert!(!allowed.contains("Bash"));
}

#[test]
fn test_resolve_coding_profile() {
    let allowed = ToolPolicy::resolve("coding", None, None).unwrap();
    assert!(allowed.contains("Read"));
    assert!(allowed.contains("Write"));
    assert!(allowed.contains("Bash"));
    assert!(!allowed.contains("SendMessage")); // not in coding
}

#[test]
fn test_resolve_unknown_profile() {
    let result = ToolPolicy::resolve("nonexistent", None, None);
    assert!(result.is_err());
    assert!(result.unwrap_err().contains("Unknown tool profile"));
}

#[test]
fn test_resolve_with_additions() {
    let allowed = ToolPolicy::resolve("minimal", Some(&["custom_tool"]), None).unwrap();
    assert!(allowed.contains("custom_tool"));
    assert!(allowed.contains("Read"));
}

#[test]
fn test_resolve_with_exclusions() {
    let allowed = ToolPolicy::resolve("full", None, Some(&["Bash"])).unwrap();
    assert!(!allowed.contains("Bash"));
    assert!(allowed.contains("Read"));
}

#[test]
fn test_resolve_exclusion_overrides_always_allowed() {
    let allowed = ToolPolicy::resolve("minimal", None, Some(&["TaskStop"])).unwrap();
    assert!(!allowed.contains("TaskStop"));
}

#[test]
fn test_get_profile_names() {
    let names = ToolPolicy::get_profile_names();
    assert!(names.contains(&"minimal"));
    assert!(names.contains(&"full"));
    assert!(names.contains(&"coding"));
    assert!(names.contains(&"review"));
}

#[test]
fn test_get_group_names() {
    let names = ToolPolicy::get_group_names();
    assert!(names.contains(&"group:read"));
    assert!(names.contains(&"group:write"));
    assert!(names.contains(&"group:process"));
}

#[test]
fn test_get_tools_in_group() {
    let tools = ToolPolicy::get_tools_in_group("group:read");
    assert!(tools.contains("Read"));
    assert!(tools.contains("Grep"));
    assert!(!tools.contains("Write"));
}

#[test]
fn test_get_tools_in_unknown_group() {
    let tools = ToolPolicy::get_tools_in_group("group:nonexistent");
    assert!(tools.is_empty());
}

#[test]
fn test_profile_descriptions() {
    assert_eq!(
        ToolPolicy::get_profile_description("minimal"),
        "Read-only tools + meta tools (for planning/exploration)"
    );
    assert_eq!(
        ToolPolicy::get_profile_description("full"),
        "All available tools (default)"
    );
    assert_eq!(
        ToolPolicy::get_profile_description("unknown"),
        "Unknown profile"
    );
}

#[test]
fn test_always_allowed_in_all_profiles() {
    for profile in &["minimal", "review", "coding", "full"] {
        let allowed = ToolPolicy::resolve(profile, None, None).unwrap();
        assert!(
            allowed.contains("TaskStop"),
            "TaskStop missing from {profile}"
        );
        assert!(
            allowed.contains("AskUserQuestion"),
            "AskUserQuestion missing from {profile}"
        );
    }
}
