use super::*;
use std::fs;
use std::sync::Arc;

fn setup_templates(dir: &std::path::Path) {
    let main_dir = dir.join("system/main");
    fs::create_dir_all(&main_dir).unwrap();

    fs::write(main_dir.join("section-a.md"), "# Section A\nContent A").unwrap();
    fs::write(main_dir.join("section-b.md"), "# Section B\nContent B").unwrap();
    fs::write(
        main_dir.join("section-c.md"),
        "<!-- frontmatter: true -->\n# Section C\nContent C",
    )
    .unwrap();
    fs::write(main_dir.join("section-d.md"), "# Dynamic\nDynamic content").unwrap();
}

#[test]
fn test_compose_basic() {
    let dir = tempfile::TempDir::new().unwrap();
    setup_templates(dir.path());

    let mut composer = PromptComposer::new(dir.path());
    composer.register_section("a", "system/main/section-a.md", None, 10, true);
    composer.register_section("b", "system/main/section-b.md", None, 20, true);

    let result = composer.compose(&HashMap::new());
    assert!(result.contains("Content A"));
    assert!(result.contains("Content B"));
    // A should come before B (lower priority)
    assert!(result.find("Content A") < result.find("Content B"));
}

#[test]
fn test_compose_priority_ordering() {
    let dir = tempfile::TempDir::new().unwrap();
    setup_templates(dir.path());

    let mut composer = PromptComposer::new(dir.path());
    // Register in reverse order
    composer.register_section("b", "system/main/section-b.md", None, 20, true);
    composer.register_section("a", "system/main/section-a.md", None, 10, true);

    let result = composer.compose(&HashMap::new());
    assert!(result.find("Content A") < result.find("Content B"));
}

#[test]
fn test_compose_with_condition() {
    let dir = tempfile::TempDir::new().unwrap();
    setup_templates(dir.path());

    let mut composer = PromptComposer::new(dir.path());
    composer.register_section("a", "system/main/section-a.md", None, 10, true);
    composer.register_section(
        "b",
        "system/main/section-b.md",
        Some(ctx_bool("show_b")),
        20,
        true,
    );

    // Without condition met
    let result = composer.compose(&HashMap::new());
    assert!(result.contains("Content A"));
    assert!(!result.contains("Content B"));

    // With condition met
    let mut ctx = HashMap::new();
    ctx.insert("show_b".to_string(), serde_json::json!(true));
    let result = composer.compose(&ctx);
    assert!(result.contains("Content A"));
    assert!(result.contains("Content B"));
}

#[test]
fn test_compose_strips_frontmatter() {
    let dir = tempfile::TempDir::new().unwrap();
    setup_templates(dir.path());

    let mut composer = PromptComposer::new(dir.path());
    composer.register_section("c", "system/main/section-c.md", None, 10, true);

    let result = composer.compose(&HashMap::new());
    assert!(!result.contains("frontmatter"));
    assert!(result.contains("Content C"));
}

#[test]
fn test_compose_two_part() {
    let dir = tempfile::TempDir::new().unwrap();
    setup_templates(dir.path());

    let mut composer = PromptComposer::new(dir.path());
    composer.register_section("a", "system/main/section-a.md", None, 10, true);
    composer.register_section("d", "system/main/section-d.md", None, 20, false);

    let (stable, dynamic) = composer.compose_two_part(&HashMap::new());
    assert!(stable.contains("Content A"));
    assert!(!stable.contains("Dynamic content"));
    assert!(dynamic.contains("Dynamic content"));
    assert!(!dynamic.contains("Content A"));
}

#[test]
fn test_compose_missing_file() {
    let dir = tempfile::TempDir::new().unwrap();

    let mut composer = PromptComposer::new(dir.path());
    composer.register_section("missing", "nonexistent.md", None, 10, true);

    let result = composer.compose(&HashMap::new());
    assert!(result.is_empty());
}

#[test]
fn test_strip_frontmatter() {
    assert_eq!(
        strip_frontmatter("<!-- key: value -->\n# Title\nContent"),
        "# Title\nContent"
    );
    assert_eq!(strip_frontmatter("No frontmatter"), "No frontmatter");
    assert_eq!(strip_frontmatter(""), "");
}

#[test]
fn test_section_count_and_names() {
    let composer_dir = tempfile::TempDir::new().unwrap();
    let mut composer = PromptComposer::new(composer_dir.path());
    composer.register_simple("alpha", "alpha.md");
    composer.register_simple("beta", "beta.md");

    assert_eq!(composer.section_count(), 2);
    let names = composer.section_names();
    assert!(names.contains(&"alpha"));
    assert!(names.contains(&"beta"));
}

#[test]
fn test_substitute_variables_basic() {
    let mut vars = HashMap::new();
    vars.insert("name".to_string(), "world".to_string());
    assert_eq!(
        substitute_variables("Hello {{name}}!", &vars),
        "Hello world!"
    );
}

#[test]
fn test_substitute_variables_multiple() {
    let mut vars = HashMap::new();
    vars.insert("session_id".to_string(), "abc-123".to_string());
    vars.insert("path".to_string(), "/home/user".to_string());

    let template = "Session {{session_id}} at {{path}}";
    assert_eq!(
        substitute_variables(template, &vars),
        "Session abc-123 at /home/user"
    );
}

#[test]
fn test_substitute_variables_missing_left_as_is() {
    let vars = HashMap::new();
    assert_eq!(
        substitute_variables("Hello {{unknown}}!", &vars),
        "Hello {{unknown}}!"
    );
}

#[test]
fn test_substitute_variables_no_placeholders() {
    let vars = HashMap::new();
    assert_eq!(substitute_variables("No vars here", &vars), "No vars here");
}

#[test]
fn test_compose_with_vars() {
    let dir = tempfile::TempDir::new().unwrap();
    let main_dir = dir.path().join("system/main");
    fs::create_dir_all(&main_dir).unwrap();
    fs::write(
        main_dir.join("template.md"),
        "Session: {{session_id}}\nPath: {{path}}",
    )
    .unwrap();

    let mut composer = PromptComposer::new(dir.path());
    composer.register_section("t", "system/main/template.md", None, 10, true);

    let mut vars = HashMap::new();
    vars.insert("session_id".to_string(), "xyz-789".to_string());
    vars.insert("path".to_string(), "/workspace".to_string());

    let result = composer.compose_with_vars(&HashMap::new(), &vars);
    assert!(result.contains("Session: xyz-789"));
    assert!(result.contains("Path: /workspace"));
}

#[test]
fn test_compose_two_part_with_vars() {
    let dir = tempfile::TempDir::new().unwrap();
    let main_dir = dir.path().join("test");
    fs::create_dir_all(&main_dir).unwrap();
    fs::write(main_dir.join("stable.md"), "Stable {{key}}").unwrap();
    fs::write(main_dir.join("dynamic.md"), "Dynamic {{key}}").unwrap();

    let mut composer = PromptComposer::new(dir.path());
    composer.register_section("s", "test/stable.md", None, 10, true);
    composer.register_section("d", "test/dynamic.md", None, 20, false);

    let mut vars = HashMap::new();
    vars.insert("key".to_string(), "value".to_string());

    let (stable, dynamic) = composer.compose_two_part_with_vars(&HashMap::new(), &vars);
    assert_eq!(stable, "Stable value");
    assert_eq!(dynamic, "Dynamic value");
}

#[test]
fn test_embedded_templates_used_by_default_composer() {
    // Use a temp dir that has NO files — embedded should still resolve
    let dir = tempfile::TempDir::new().unwrap();
    let mut composer = create_default_composer(dir.path());

    // Compose without any conditions to get the always-included sections
    let result = composer.compose(&HashMap::new());

    // The security policy section is always included (no condition) and should
    // come from embedded templates even though the filesystem dir is empty.
    assert!(
        result.contains("Security Policy"),
        "Expected embedded security policy template"
    );
}

// ─── Section Cache Tests ─────────────────────────────────────────────

#[test]
fn test_static_section_cached_across_composes() {
    use std::sync::atomic::{AtomicUsize, Ordering};

    let call_count = Arc::new(AtomicUsize::new(0));
    let cc = Arc::clone(&call_count);

    let mut composer = PromptComposer::new("/dev/null");
    composer.register_dynamic_section(
        "counter",
        CachePolicy::Static,
        10,
        None,
        Box::new(move || {
            cc.fetch_add(1, Ordering::SeqCst);
            Some("static content".to_string())
        }),
    );

    let ctx = HashMap::new();
    let r1 = composer.compose(&ctx);
    let r2 = composer.compose(&ctx);

    assert_eq!(r1, "static content");
    assert_eq!(r2, "static content");
    // Provider should only be called once — second compose uses cache
    assert_eq!(call_count.load(Ordering::SeqCst), 1);
}

#[test]
fn test_cached_section_survives_compose_but_cleared_by_clear_cache() {
    use std::sync::atomic::{AtomicUsize, Ordering};

    let call_count = Arc::new(AtomicUsize::new(0));
    let cc = Arc::clone(&call_count);

    let mut composer = PromptComposer::new("/dev/null");
    composer.register_dynamic_section(
        "dynamic",
        CachePolicy::Cached,
        10,
        None,
        Box::new(move || {
            let n = cc.fetch_add(1, Ordering::SeqCst);
            Some(format!("call-{n}"))
        }),
    );

    let ctx = HashMap::new();
    let r1 = composer.compose(&ctx);
    assert_eq!(r1, "call-0");

    // Second compose should use cache
    let r2 = composer.compose(&ctx);
    assert_eq!(r2, "call-0");
    assert_eq!(call_count.load(Ordering::SeqCst), 1);

    // After clear_cache(), Cached sections recompute
    composer.clear_cache();
    let r3 = composer.compose(&ctx);
    assert_eq!(r3, "call-1");
    assert_eq!(call_count.load(Ordering::SeqCst), 2);
}

#[test]
fn test_uncached_section_recomputes_every_turn() {
    use std::sync::atomic::{AtomicUsize, Ordering};

    let call_count = Arc::new(AtomicUsize::new(0));
    let cc = Arc::clone(&call_count);

    let mut composer = PromptComposer::new("/dev/null");
    composer.register_dynamic_section(
        "volatile",
        CachePolicy::Uncached,
        10,
        None,
        Box::new(move || {
            let n = cc.fetch_add(1, Ordering::SeqCst);
            Some(format!("turn-{n}"))
        }),
    );

    let ctx = HashMap::new();
    assert_eq!(composer.compose(&ctx), "turn-0");
    assert_eq!(composer.compose(&ctx), "turn-1");
    assert_eq!(composer.compose(&ctx), "turn-2");
    assert_eq!(call_count.load(Ordering::SeqCst), 3);
}

#[test]
fn test_static_survives_clear_cache_but_not_clear_all() {
    use std::sync::atomic::{AtomicUsize, Ordering};

    let static_count = Arc::new(AtomicUsize::new(0));
    let sc = Arc::clone(&static_count);

    let mut composer = PromptComposer::new("/dev/null");
    composer.register_dynamic_section(
        "stable",
        CachePolicy::Static,
        10,
        None,
        Box::new(move || {
            sc.fetch_add(1, Ordering::SeqCst);
            Some("stable".to_string())
        }),
    );

    let ctx = HashMap::new();
    composer.compose(&ctx);
    assert_eq!(static_count.load(Ordering::SeqCst), 1);

    // clear_cache only clears Cached, not Static
    composer.clear_cache();
    composer.compose(&ctx);
    assert_eq!(static_count.load(Ordering::SeqCst), 1);

    // clear_all_cache clears everything
    composer.clear_all_cache();
    composer.compose(&ctx);
    assert_eq!(static_count.load(Ordering::SeqCst), 2);
}

#[test]
fn test_section_override_takes_precedence() {
    let mut composer = PromptComposer::new("/dev/null");
    composer.register_dynamic_section(
        "mcp",
        CachePolicy::Uncached,
        10,
        None,
        Box::new(|| None), // No-op provider
    );

    let ctx = HashMap::new();

    // Without override, section produces nothing
    assert_eq!(composer.compose(&ctx), "");

    // With override, section produces the override content
    composer.set_section_override("mcp", Some("MCP tools available".to_string()));
    assert_eq!(composer.compose(&ctx), "MCP tools available");

    // Override is consumed — next compose goes back to provider
    assert_eq!(composer.compose(&ctx), "");
}

#[test]
fn test_content_provider_takes_precedence_over_template() {
    let dir = tempfile::TempDir::new().unwrap();
    setup_templates(dir.path());

    let mut composer = PromptComposer::new(dir.path());
    // Register with a template path that exists, but also a content provider
    composer.register_dynamic_section(
        "override",
        CachePolicy::Static,
        10,
        None,
        Box::new(|| Some("from provider".to_string())),
    );

    let result = composer.compose(&HashMap::new());
    assert_eq!(result, "from provider");
}

#[test]
fn test_two_part_with_cache_policies() {
    let mut composer = PromptComposer::new("/dev/null");
    composer.register_dynamic_section(
        "static_sec",
        CachePolicy::Static,
        10,
        None,
        Box::new(|| Some("static-part".to_string())),
    );
    composer.register_dynamic_section(
        "cached_sec",
        CachePolicy::Cached,
        20,
        None,
        Box::new(|| Some("cached-part".to_string())),
    );
    composer.register_dynamic_section(
        "uncached_sec",
        CachePolicy::Uncached,
        30,
        None,
        Box::new(|| Some("uncached-part".to_string())),
    );

    let ctx = HashMap::new();
    let (stable, dynamic) = composer.compose_two_part(&ctx);

    // Static and Cached go to stable
    assert!(stable.contains("static-part"));
    assert!(stable.contains("cached-part"));
    assert!(!stable.contains("uncached-part"));

    // Uncached goes to dynamic
    assert!(dynamic.contains("uncached-part"));
    assert!(!dynamic.contains("static-part"));
}
