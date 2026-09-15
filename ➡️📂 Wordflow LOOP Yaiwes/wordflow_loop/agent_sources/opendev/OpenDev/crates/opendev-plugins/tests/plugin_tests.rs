//! Comprehensive tests for the opendev-plugins crate.

use opendev_plugins::manager::*;
use opendev_plugins::models::*;
use std::fs;
use std::path::PathBuf;
use tempfile::TempDir;

/// Helper: create a PluginManager rooted in a temp dir with the expected directory structure.
fn make_manager(tmp: &TempDir) -> PluginManager {
    let working_dir = tmp.path().to_path_buf();

    // Override paths to use the temp dir for everything
    let mut manager = PluginManager::new(Some(working_dir.clone()));
    manager.paths = PluginPaths {
        global_plugins_dir: tmp.path().join("global_plugins"),
        project_plugins_dir: tmp.path().join("project_plugins"),
        global_marketplaces_dir: tmp.path().join("marketplaces"),
        global_plugin_cache_dir: tmp.path().join("global_plugins").join("cache"),
        known_marketplaces_file: tmp.path().join("marketplaces.json"),
        global_installed_plugins_file: tmp.path().join("installed_plugins.json"),
        project_installed_plugins_file: tmp.path().join("project_installed_plugins.json"),
    };
    manager
}

/// Helper: create a plugin directory with a manifest.json.
fn create_plugin_dir(base: &std::path::Path, name: &str, version: &str) -> PathBuf {
    let dir = base.join(name);
    fs::create_dir_all(&dir).unwrap();
    let manifest = serde_json::json!({
        "name": name,
        "version": version,
        "description": format!("Test plugin {}", name),
        "author": "Test Author",
        "tools": [{"name": "test_tool", "description": "A test tool"}],
        "prompts": [{"name": "test_prompt", "description": "A test prompt", "template": "Hello"}],
        "dependencies": [],
        "skills": ["skill_a"]
    });
    fs::write(
        dir.join("manifest.json"),
        serde_json::to_string_pretty(&manifest).unwrap(),
    )
    .unwrap();
    dir
}

/// Helper: create a marketplace structure with plugins.
fn create_marketplace(base: &std::path::Path, marketplace_name: &str, plugin_names: &[&str]) {
    let marketplace_dir = base.join(marketplace_name);
    let plugins_dir = marketplace_dir.join("plugins");
    fs::create_dir_all(&plugins_dir).unwrap();

    for name in plugin_names {
        create_plugin_dir(&plugins_dir, name, "1.0.0");
    }

    // Write marketplace.json
    let catalog = serde_json::json!({
        "plugins": plugin_names,
        "auto_discovered": false
    });
    fs::write(
        marketplace_dir.join("marketplace.json"),
        serde_json::to_string_pretty(&catalog).unwrap(),
    )
    .unwrap();
}

// ── Model tests ────────────────────────────────────────────────

#[test]
fn test_plugin_manifest_serialization() {
    let manifest = PluginManifest {
        name: "my-plugin".into(),
        version: "1.2.3".into(),
        description: "A great plugin".into(),
        author: Some("Author".into()),
        tools: vec![ToolDefinition {
            name: "tool1".into(),
            description: "Does things".into(),
            parameters: serde_json::json!({}),
        }],
        prompts: vec![PromptTemplate {
            name: "prompt1".into(),
            description: "A prompt".into(),
            template: "Hello {{name}}".into(),
        }],
        dependencies: vec!["dep1".into()],
        skills: vec!["skill1".into()],
        repository: Some("https://github.com/test/repo".into()),
        license: Some("MIT".into()),
    };

    let json = serde_json::to_string(&manifest).unwrap();
    let deserialized: PluginManifest = serde_json::from_str(&json).unwrap();
    assert_eq!(deserialized.name, "my-plugin");
    assert_eq!(deserialized.version, "1.2.3");
    assert_eq!(deserialized.tools.len(), 1);
    assert_eq!(deserialized.prompts.len(), 1);
    assert_eq!(deserialized.dependencies, vec!["dep1"]);
}

#[test]
fn test_plugin_source_variants() {
    let git = PluginSource::Git {
        url: "https://github.com/test/repo".into(),
        branch: "main".into(),
    };
    let local = PluginSource::Local {
        path: PathBuf::from("/tmp/plugin"),
    };
    let marketplace = PluginSource::Marketplace {
        marketplace: "default".into(),
    };

    // Serialize and deserialize each variant
    for source in [&git, &local, &marketplace] {
        let json = serde_json::to_string(source).unwrap();
        let back: PluginSource = serde_json::from_str(&json).unwrap();
        assert_eq!(&back, source);
    }
}

#[test]
fn test_plugin_status_variants() {
    let installed = PluginStatus::Installed;
    let disabled = PluginStatus::Disabled;
    let error = PluginStatus::Error("something broke".into());

    let json = serde_json::to_string(&installed).unwrap();
    assert!(json.contains("installed"));

    let json = serde_json::to_string(&disabled).unwrap();
    assert!(json.contains("disabled"));

    let json = serde_json::to_string(&error).unwrap();
    assert!(json.contains("something broke"));
}

#[test]
fn test_installed_plugins_registry() {
    let mut registry = InstalledPlugins::default();
    assert!(registry.plugins.is_empty());

    let config = PluginConfig {
        name: "test-plugin".into(),
        version: "1.0.0".into(),
        source: PluginSource::Marketplace {
            marketplace: "my-market".into(),
        },
        status: PluginStatus::Installed,
        scope: PluginScope::User,
        enabled: true,
        path: PathBuf::from("/tmp/test-plugin"),
        installed_at: chrono::Utc::now(),
        marketplace: Some("my-market".into()),
    };

    registry.add(config.clone());
    assert_eq!(registry.plugins.len(), 1);
    assert!(registry.get("my-market", "test-plugin").is_some());

    // Remove
    let removed = registry.remove("my-market", "test-plugin");
    assert!(removed.is_some());
    assert!(registry.plugins.is_empty());
}

#[test]
fn test_installed_plugins_make_key() {
    assert_eq!(
        InstalledPlugins::make_key("market", "plugin"),
        "market:plugin"
    );
}

// ── Manager tests ──────────────────────────────────────────────

#[test]
fn test_discover_plugins_empty_dir() {
    let tmp = TempDir::new().unwrap();
    let manager = make_manager(&tmp);

    let manifests = manager.discover_plugins().unwrap();
    assert!(manifests.is_empty());
}

#[test]
fn test_discover_plugins_finds_manifests() {
    let tmp = TempDir::new().unwrap();
    let manager = make_manager(&tmp);

    // Create plugins in the global dir
    fs::create_dir_all(&manager.paths.global_plugins_dir).unwrap();
    create_plugin_dir(&manager.paths.global_plugins_dir, "alpha", "0.1.0");
    create_plugin_dir(&manager.paths.global_plugins_dir, "beta", "0.2.0");

    let manifests = manager.discover_plugins().unwrap();
    assert_eq!(manifests.len(), 2);

    let names: Vec<&str> = manifests.iter().map(|m| m.name.as_str()).collect();
    assert!(names.contains(&"alpha"));
    assert!(names.contains(&"beta"));
}

#[test]
fn test_discover_plugins_project_and_global() {
    let tmp = TempDir::new().unwrap();
    let manager = make_manager(&tmp);

    fs::create_dir_all(&manager.paths.global_plugins_dir).unwrap();
    fs::create_dir_all(&manager.paths.project_plugins_dir).unwrap();
    create_plugin_dir(&manager.paths.global_plugins_dir, "global-plugin", "1.0.0");
    create_plugin_dir(
        &manager.paths.project_plugins_dir,
        "project-plugin",
        "1.0.0",
    );

    let manifests = manager.discover_plugins().unwrap();
    assert_eq!(manifests.len(), 2);
}

#[test]
fn test_load_manifest_from_file() {
    let tmp = TempDir::new().unwrap();
    let manager = make_manager(&tmp);

    let dir = create_plugin_dir(tmp.path(), "test-plugin", "2.0.0");
    let manifest = manager.load_manifest(&dir).unwrap();
    assert_eq!(manifest.name, "test-plugin");
    assert_eq!(manifest.version, "2.0.0");
    assert_eq!(manifest.author.as_deref(), Some("Test Author"));
}

#[test]
fn test_load_manifest_missing() {
    let tmp = TempDir::new().unwrap();
    let manager = make_manager(&tmp);

    let empty_dir = tmp.path().join("empty");
    fs::create_dir_all(&empty_dir).unwrap();

    let result = manager.load_manifest(&empty_dir);
    assert!(result.is_err());
    match result.unwrap_err() {
        PluginError::InvalidPlugin(msg) => assert!(msg.contains("No manifest.json")),
        other => panic!("Expected InvalidPlugin, got {:?}", other),
    }
}

#[test]
fn test_known_marketplaces_persistence() {
    let tmp = TempDir::new().unwrap();
    let manager = make_manager(&tmp);

    // Initially empty
    let loaded = manager.load_known_marketplaces().unwrap();
    assert!(loaded.marketplaces.is_empty());

    // Save some marketplaces
    let mut marketplaces = KnownMarketplaces::default();
    marketplaces.marketplaces.insert(
        "test-market".into(),
        MarketplaceInfo {
            name: "test-market".into(),
            url: "https://github.com/test/market".into(),
            branch: "main".into(),
            added_at: chrono::Utc::now(),
            last_updated: None,
        },
    );
    manager.save_known_marketplaces(&marketplaces).unwrap();

    // Load back
    let loaded = manager.load_known_marketplaces().unwrap();
    assert_eq!(loaded.marketplaces.len(), 1);
    assert!(loaded.marketplaces.contains_key("test-market"));
}

#[test]
fn test_installed_plugins_persistence() {
    let tmp = TempDir::new().unwrap();
    let manager = make_manager(&tmp);

    let mut plugins = InstalledPlugins::default();
    plugins.add(PluginConfig {
        name: "test".into(),
        version: "1.0.0".into(),
        source: PluginSource::Local {
            path: PathBuf::from("/tmp"),
        },
        status: PluginStatus::Installed,
        scope: PluginScope::User,
        enabled: true,
        path: PathBuf::from("/tmp/test"),
        installed_at: chrono::Utc::now(),
        marketplace: Some("local".into()),
    });

    manager
        .save_installed_plugins(&plugins, PluginScope::User)
        .unwrap();
    let loaded = manager.load_installed_plugins(PluginScope::User).unwrap();
    assert_eq!(loaded.plugins.len(), 1);
}

#[test]
fn test_enable_disable_plugin() {
    let tmp = TempDir::new().unwrap();
    let manager = make_manager(&tmp);

    // Register a plugin
    let mut plugins = InstalledPlugins::default();
    plugins.add(PluginConfig {
        name: "toggleable".into(),
        version: "1.0.0".into(),
        source: PluginSource::Marketplace {
            marketplace: "market".into(),
        },
        status: PluginStatus::Installed,
        scope: PluginScope::User,
        enabled: true,
        path: PathBuf::from("/tmp/toggleable"),
        installed_at: chrono::Utc::now(),
        marketplace: Some("market".into()),
    });
    manager
        .save_installed_plugins(&plugins, PluginScope::User)
        .unwrap();

    // Disable
    manager
        .disable_plugin("toggleable", "market", PluginScope::User)
        .unwrap();
    let loaded = manager.load_installed_plugins(PluginScope::User).unwrap();
    let p = loaded.get("market", "toggleable").unwrap();
    assert!(!p.enabled);
    assert_eq!(p.status, PluginStatus::Disabled);

    // Re-enable
    manager
        .enable_plugin("toggleable", "market", PluginScope::User)
        .unwrap();
    let loaded = manager.load_installed_plugins(PluginScope::User).unwrap();
    let p = loaded.get("market", "toggleable").unwrap();
    assert!(p.enabled);
    assert_eq!(p.status, PluginStatus::Installed);
}

#[test]
fn test_enable_nonexistent_plugin_returns_error() {
    let tmp = TempDir::new().unwrap();
    let manager = make_manager(&tmp);

    let result = manager.enable_plugin("ghost", "market", PluginScope::User);
    assert!(result.is_err());
}

// ── Marketplace tests ──────────────────────────────────────────

#[test]
fn test_marketplace_catalog_auto_discover() {
    let tmp = TempDir::new().unwrap();
    let manager = make_manager(&tmp);

    // Register a fake marketplace
    let marketplace_name = "test-market";
    let marketplace_dir = manager.paths.global_marketplaces_dir.join(marketplace_name);
    let plugins_dir = marketplace_dir.join("plugins");
    fs::create_dir_all(&plugins_dir).unwrap();
    create_plugin_dir(&plugins_dir, "plug-a", "1.0.0");
    create_plugin_dir(&plugins_dir, "plug-b", "1.0.0");

    // Register the marketplace
    let mut marketplaces = KnownMarketplaces::default();
    marketplaces.marketplaces.insert(
        marketplace_name.into(),
        MarketplaceInfo {
            name: marketplace_name.into(),
            url: "https://example.com/market".into(),
            branch: "main".into(),
            added_at: chrono::Utc::now(),
            last_updated: None,
        },
    );
    manager.save_known_marketplaces(&marketplaces).unwrap();

    // Get catalog (auto-discover, no marketplace.json)
    let catalog = manager.get_marketplace_catalog(marketplace_name).unwrap();
    assert!(catalog.auto_discovered);
    assert_eq!(catalog.plugins.len(), 2);
}

#[test]
fn test_marketplace_catalog_from_json() {
    let tmp = TempDir::new().unwrap();
    let manager = make_manager(&tmp);

    let marketplace_name = "json-market";
    create_marketplace(
        &manager.paths.global_marketplaces_dir,
        marketplace_name,
        &["alpha", "beta"],
    );

    // Register the marketplace
    let mut marketplaces = KnownMarketplaces::default();
    marketplaces.marketplaces.insert(
        marketplace_name.into(),
        MarketplaceInfo {
            name: marketplace_name.into(),
            url: "https://example.com/market".into(),
            branch: "main".into(),
            added_at: chrono::Utc::now(),
            last_updated: None,
        },
    );
    manager.save_known_marketplaces(&marketplaces).unwrap();

    let catalog = manager.get_marketplace_catalog(marketplace_name).unwrap();
    assert!(!catalog.auto_discovered);
    assert_eq!(catalog.plugins.len(), 2);
}

#[test]
fn test_list_marketplace_plugins() {
    let tmp = TempDir::new().unwrap();
    let manager = make_manager(&tmp);

    let marketplace_name = "list-market";
    create_marketplace(
        &manager.paths.global_marketplaces_dir,
        marketplace_name,
        &["plugx", "plugy"],
    );

    let mut marketplaces = KnownMarketplaces::default();
    marketplaces.marketplaces.insert(
        marketplace_name.into(),
        MarketplaceInfo {
            name: marketplace_name.into(),
            url: "https://example.com/market".into(),
            branch: "main".into(),
            added_at: chrono::Utc::now(),
            last_updated: None,
        },
    );
    manager.save_known_marketplaces(&marketplaces).unwrap();

    // list_marketplace_plugins expects plugin.json, but we wrote manifest.json.
    // The plugins will fall through to the default metadata branch.
    let plugins = manager.list_marketplace_plugins(marketplace_name).unwrap();
    assert_eq!(plugins.len(), 2);
}

#[test]
fn test_search_marketplace() {
    let tmp = TempDir::new().unwrap();
    let manager = make_manager(&tmp);

    let marketplace_name = "search-market";
    create_marketplace(
        &manager.paths.global_marketplaces_dir,
        marketplace_name,
        &["formatter", "linter", "debugger"],
    );

    let mut marketplaces = KnownMarketplaces::default();
    marketplaces.marketplaces.insert(
        marketplace_name.into(),
        MarketplaceInfo {
            name: marketplace_name.into(),
            url: "https://example.com/market".into(),
            branch: "main".into(),
            added_at: chrono::Utc::now(),
            last_updated: None,
        },
    );
    manager.save_known_marketplaces(&marketplaces).unwrap();

    let results = manager
        .search_marketplace(marketplace_name, "lint")
        .unwrap();
    assert_eq!(results.len(), 1);
    assert_eq!(results[0].name, "linter");

    let results = manager.search_marketplace(marketplace_name, "er").unwrap();
    // "formatter", "linter", "debugger" all contain "er"
    assert_eq!(results.len(), 3);
}

#[test]
fn test_remove_marketplace_not_found() {
    let tmp = TempDir::new().unwrap();
    let manager = make_manager(&tmp);

    let result = manager.remove_marketplace("nonexistent");
    assert!(result.is_err());
    match result.unwrap_err() {
        PluginError::MarketplaceNotFound(name) => assert_eq!(name, "nonexistent"),
        other => panic!("Expected MarketplaceNotFound, got {:?}", other),
    }
}

// ── Utility tests ──────────────────────────────────────────────

#[test]
fn test_extract_name_from_url() {
    assert_eq!(
        PluginManager::extract_name_from_url("https://github.com/user/my-plugins.git"),
        "my-plugins"
    );
    assert_eq!(
        PluginManager::extract_name_from_url("https://github.com/user/swecli-marketplace"),
        "marketplace" // swecli- prefix removed -> "marketplace"; -marketplace$ doesn't match
    );
    assert_eq!(
        PluginManager::extract_name_from_url("https://github.com/user/awesome-tools"),
        "awesome-tools"
    );
}

#[test]
fn test_parse_skill_metadata() {
    let tmp = TempDir::new().unwrap();
    let skill_file = tmp.path().join("SKILL.md");
    fs::write(
        &skill_file,
        "---\nname: my-skill\ndescription: Does cool things\n---\n# My Skill\n",
    )
    .unwrap();

    let (name, desc) = PluginManager::parse_skill_metadata(&skill_file);
    assert_eq!(name, "my-skill");
    assert_eq!(desc, "Does cool things");
}

#[test]
fn test_parse_skill_metadata_missing_file() {
    let (name, desc) = PluginManager::parse_skill_metadata(&PathBuf::from("/nonexistent/SKILL.md"));
    assert!(name.is_empty());
    assert!(desc.is_empty());
}

#[test]
fn test_discover_skills_in_dir() {
    let tmp = TempDir::new().unwrap();
    let plugin_dir = tmp.path().join("plugin");
    let skills_dir = plugin_dir.join("skills");
    let skill_a = skills_dir.join("skill_a");
    let skill_b = skills_dir.join("skill_b");

    fs::create_dir_all(&skill_a).unwrap();
    fs::create_dir_all(&skill_b).unwrap();
    fs::write(skill_a.join("SKILL.md"), "---\nname: A\n---").unwrap();
    fs::write(skill_b.join("SKILL.md"), "---\nname: B\n---").unwrap();

    let skills = PluginManager::discover_skills_in_dir(&plugin_dir);
    assert_eq!(skills.len(), 2);
}

#[test]
fn test_copy_dir_recursive() {
    let tmp = TempDir::new().unwrap();
    let src = tmp.path().join("src_dir");
    let dst = tmp.path().join("dst_dir");

    fs::create_dir_all(src.join("sub")).unwrap();
    fs::write(src.join("file.txt"), "hello").unwrap();
    fs::write(src.join("sub").join("nested.txt"), "world").unwrap();

    copy_dir_recursive(&src, &dst).unwrap();

    assert!(dst.join("file.txt").exists());
    assert!(dst.join("sub").join("nested.txt").exists());
    assert_eq!(fs::read_to_string(dst.join("file.txt")).unwrap(), "hello");
    assert_eq!(
        fs::read_to_string(dst.join("sub").join("nested.txt")).unwrap(),
        "world"
    );
}

#[test]
fn test_marketplace_catalog_serde() {
    let catalog = MarketplaceCatalog {
        plugins: vec!["a".into(), "b".into()],
        auto_discovered: true,
    };
    let json = serde_json::to_string(&catalog).unwrap();
    let back: MarketplaceCatalog = serde_json::from_str(&json).unwrap();
    assert_eq!(back.plugins, vec!["a", "b"]);
    assert!(back.auto_discovered);
}

#[test]
fn test_install_plugin_marketplace_not_found() {
    let tmp = TempDir::new().unwrap();
    let manager = make_manager(&tmp);

    let result = manager.install_plugin("whatever", "nonexistent", PluginScope::User);
    assert!(result.is_err());
    match result.unwrap_err() {
        PluginError::MarketplaceNotFound(name) => assert_eq!(name, "nonexistent"),
        other => panic!("Expected MarketplaceNotFound, got {:?}", other),
    }
}

#[test]
fn test_uninstall_plugin_not_found() {
    let tmp = TempDir::new().unwrap();
    let manager = make_manager(&tmp);

    let result = manager.uninstall_plugin("ghost", "market", PluginScope::User);
    assert!(result.is_err());
}

#[test]
fn test_install_and_uninstall_plugin() {
    let tmp = TempDir::new().unwrap();
    let manager = make_manager(&tmp);

    // Set up a marketplace with a plugin
    let marketplace_name = "test-market";
    create_marketplace(
        &manager.paths.global_marketplaces_dir,
        marketplace_name,
        &["my-plugin"],
    );

    let mut marketplaces = KnownMarketplaces::default();
    marketplaces.marketplaces.insert(
        marketplace_name.into(),
        MarketplaceInfo {
            name: marketplace_name.into(),
            url: "https://example.com/market".into(),
            branch: "main".into(),
            added_at: chrono::Utc::now(),
            last_updated: None,
        },
    );
    manager.save_known_marketplaces(&marketplaces).unwrap();

    // Install
    let config = manager
        .install_plugin("my-plugin", marketplace_name, PluginScope::User)
        .unwrap();
    assert_eq!(config.name, "my-plugin");
    assert!(config.enabled);
    assert!(config.path.exists());

    // Verify listed
    let installed = manager.list_installed(Some(PluginScope::User)).unwrap();
    assert_eq!(installed.len(), 1);

    // Uninstall
    manager
        .uninstall_plugin("my-plugin", marketplace_name, PluginScope::User)
        .unwrap();
    let installed = manager.list_installed(Some(PluginScope::User)).unwrap();
    assert!(installed.is_empty());
}

#[test]
fn test_list_installed_merges_scopes() {
    let tmp = TempDir::new().unwrap();
    let manager = make_manager(&tmp);

    // Add a user-scope plugin
    let mut user_plugins = InstalledPlugins::default();
    user_plugins.add(PluginConfig {
        name: "user-plug".into(),
        version: "1.0.0".into(),
        source: PluginSource::Local {
            path: PathBuf::from("/tmp"),
        },
        status: PluginStatus::Installed,
        scope: PluginScope::User,
        enabled: true,
        path: PathBuf::from("/tmp/user-plug"),
        installed_at: chrono::Utc::now(),
        marketplace: Some("local".into()),
    });
    manager
        .save_installed_plugins(&user_plugins, PluginScope::User)
        .unwrap();

    // Add a project-scope plugin
    let mut project_plugins = InstalledPlugins::default();
    project_plugins.add(PluginConfig {
        name: "project-plug".into(),
        version: "1.0.0".into(),
        source: PluginSource::Local {
            path: PathBuf::from("/tmp"),
        },
        status: PluginStatus::Installed,
        scope: PluginScope::Project,
        enabled: true,
        path: PathBuf::from("/tmp/project-plug"),
        installed_at: chrono::Utc::now(),
        marketplace: Some("local".into()),
    });
    manager
        .save_installed_plugins(&project_plugins, PluginScope::Project)
        .unwrap();

    // List all
    let all = manager.list_installed(None).unwrap();
    assert_eq!(all.len(), 2);
}
