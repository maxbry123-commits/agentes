use super::*;
use std::path::PathBuf;
use tempfile::TempDir;

// ---- is_external_path tests ----

#[test]
fn test_external_path_within_workdir() {
    let tmp = TempDir::new().unwrap();
    let wd = tmp.path().canonicalize().unwrap();
    assert!(!is_external_path(&wd.join("src/main.rs"), &wd));
}

#[test]
fn test_external_path_outside_workdir() {
    let tmp = TempDir::new().unwrap();
    let wd = tmp.path().canonicalize().unwrap();
    assert!(is_external_path(Path::new("/etc/hosts"), &wd));
}

#[test]
fn test_external_path_home_dir() {
    let tmp = TempDir::new().unwrap();
    let wd = tmp.path().canonicalize().unwrap();
    if let Some(home) = dirs::home_dir() {
        // Random home subdir is external
        assert!(is_external_path(&home.join("some_project/file.rs"), &wd));
    }
}

#[test]
fn test_external_path_opendev_config_allowed() {
    let tmp = TempDir::new().unwrap();
    let wd = tmp.path().canonicalize().unwrap();
    if let Some(home) = dirs::home_dir() {
        assert!(!is_external_path(
            &home.join(".opendev/memory/test.md"),
            &wd
        ));
    }
}

#[test]
fn test_external_path_xdg_config_allowed() {
    let tmp = TempDir::new().unwrap();
    let wd = tmp.path().canonicalize().unwrap();
    if let Some(home) = dirs::home_dir() {
        assert!(!is_external_path(
            &home.join(".config/opendev/settings.toml"),
            &wd
        ));
    }
}

#[test]
fn test_external_path_tmp_allowed() {
    let tmp = TempDir::new().unwrap();
    let wd = tmp.path().canonicalize().unwrap();
    assert!(!is_external_path(Path::new("/tmp/opendev-test.txt"), &wd));
}

#[test]
fn test_external_path_var_tmp_allowed() {
    let tmp = TempDir::new().unwrap();
    let wd = tmp.path().canonicalize().unwrap();
    assert!(!is_external_path(
        Path::new("/var/tmp/opendev-test.txt"),
        &wd
    ));
}

#[test]
fn test_external_path_traversal() {
    let tmp = TempDir::new().unwrap();
    let wd = tmp.path().canonicalize().unwrap();
    // Path traversal resolves to outside workdir
    assert!(is_external_path(&wd.join("../../../etc/passwd"), &wd));
}

#[test]
fn test_external_path_sibling_project() {
    // Use a path under $HOME (not /tmp, which is always allowed by is_external_path)
    let home = dirs::home_dir().unwrap();
    let base = home.join(".opendev-test-workspace");
    let wd = base.join("my-project");
    std::fs::create_dir_all(&wd).unwrap();
    let wd = wd.canonicalize().unwrap();
    // Sibling project: resolves to ~/.opendev-test-workspace/other-project/main.rs
    assert!(is_external_path(&wd.join("../other-project/main.rs"), &wd));
    // Cleanup
    let _ = std::fs::remove_dir_all(&base);
}

#[test]
fn test_external_path_home_claude_is_external() {
    let tmp = TempDir::new().unwrap();
    let wd = tmp.path().canonicalize().unwrap();
    if let Some(home) = dirs::home_dir() {
        // ~/.claude is external (not in the allowed list)
        assert!(is_external_path(
            &home.join(".claude/skills/my-skill.md"),
            &wd
        ));
    }
}

// ---- Path normalization tests ----

#[test]
fn test_normalize_path_collapses_dotdot() {
    let result = normalize_path(Path::new("/home/user/project/../../../etc/passwd"));
    assert_eq!(result, PathBuf::from("/etc/passwd"));
}

#[test]
fn test_normalize_path_collapses_dot() {
    let result = normalize_path(Path::new("/home/user/./project/./src"));
    assert_eq!(result, PathBuf::from("/home/user/project/src"));
}

#[test]
fn test_normalize_path_preserves_root() {
    let result = normalize_path(Path::new("/../../etc"));
    assert_eq!(result, PathBuf::from("/etc"));
}

// ---- Sensitive file detection ----

#[test]
fn test_sensitive_env_file() {
    assert!(is_sensitive_file(Path::new(".env")).is_some());
    assert!(is_sensitive_file(Path::new("/project/.env")).is_some());
    assert!(is_sensitive_file(Path::new(".env.local")).is_some());
    assert!(is_sensitive_file(Path::new(".env.production")).is_some());
}

#[test]
fn test_sensitive_env_example_allowed() {
    assert!(is_sensitive_file(Path::new(".env.example")).is_none());
    assert!(is_sensitive_file(Path::new(".env.sample")).is_none());
}

#[test]
fn test_sensitive_private_keys() {
    assert!(is_sensitive_file(Path::new("server.pem")).is_some());
    assert!(is_sensitive_file(Path::new("private.key")).is_some());
    assert!(is_sensitive_file(Path::new("id_rsa")).is_some());
    assert!(is_sensitive_file(Path::new("id_ed25519")).is_some());
}

#[test]
fn test_sensitive_credentials() {
    assert!(is_sensitive_file(Path::new("credentials.json")).is_some());
    assert!(is_sensitive_file(Path::new(".npmrc")).is_some());
    assert!(is_sensitive_file(Path::new(".netrc")).is_some());
    assert!(is_sensitive_file(Path::new(".htpasswd")).is_some());
}

#[test]
fn test_sensitive_secrets_files() {
    assert!(is_sensitive_file(Path::new("app-secret.json")).is_some());
    assert!(is_sensitive_file(Path::new("secret.yaml")).is_some());
}

#[test]
fn test_non_sensitive_files() {
    assert!(is_sensitive_file(Path::new("main.rs")).is_none());
    assert!(is_sensitive_file(Path::new("README.md")).is_none());
    assert!(is_sensitive_file(Path::new("config.toml")).is_none());
    assert!(is_sensitive_file(Path::new("package.json")).is_none());
    assert!(is_sensitive_file(Path::new("Cargo.lock")).is_none());
}

#[test]
fn test_sensitive_file_outside_workdir() {
    // Sensitive file detection works regardless of path location
    assert!(is_sensitive_file(Path::new("/some/other/project/.env")).is_some());
    assert!(is_sensitive_file(Path::new("/home/user/.ssh/id_rsa")).is_some());
}

#[test]
fn test_non_sensitive_file_outside_workdir() {
    assert!(is_sensitive_file(Path::new("/var/log/app.log")).is_none());
    assert!(is_sensitive_file(Path::new("/home/user/project/main.rs")).is_none());
}
