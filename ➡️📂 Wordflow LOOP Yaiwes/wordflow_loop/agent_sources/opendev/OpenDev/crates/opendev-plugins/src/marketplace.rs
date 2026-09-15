//! Marketplace client: fetch plugin listings, search, download/install from marketplace.

use crate::manager::{PluginError, PluginManager, Result};
use crate::models::{MarketplaceCatalog, MarketplaceInfo, PluginMetadata};
use chrono::Utc;
use std::path::Path;
use tracing::info;

impl PluginManager {
    // ── Marketplace management ─────────────────────────────────

    /// Add a marketplace by recording its info and cloning its repository.
    /// In this Rust port the actual git clone is performed synchronously
    /// via `std::process::Command`.
    pub fn add_marketplace(
        &self,
        url: &str,
        name: Option<&str>,
        branch: &str,
    ) -> Result<MarketplaceInfo> {
        let name = name
            .map(String::from)
            .unwrap_or_else(|| Self::extract_name_from_url(url));

        // Check if marketplace already exists
        let mut marketplaces = self.load_known_marketplaces()?;
        if marketplaces.marketplaces.contains_key(&name) {
            return Err(PluginError::MarketplaceAlreadyExists(name));
        }

        // Prepare target directory
        let target_dir = self.paths.global_marketplaces_dir.join(&name);
        if target_dir.exists() {
            std::fs::remove_dir_all(&target_dir)?;
        }

        // Clone repository
        self.git_clone(url, branch, &target_dir)?;

        // Validate marketplace structure
        if !self.validate_marketplace(&target_dir) {
            let _ = std::fs::remove_dir_all(&target_dir);
            return Err(PluginError::InvalidPlugin(
                "Invalid marketplace: no marketplace.json, plugins/, or skills/ directory found"
                    .to_string(),
            ));
        }

        // Register marketplace
        let info = MarketplaceInfo {
            name: name.clone(),
            url: url.to_string(),
            branch: branch.to_string(),
            added_at: Utc::now(),
            last_updated: Some(Utc::now()),
        };
        marketplaces.marketplaces.insert(name.clone(), info.clone());
        self.save_known_marketplaces(&marketplaces)?;

        info!(marketplace = %name, "Marketplace added");
        Ok(info)
    }

    /// Remove a marketplace.
    pub fn remove_marketplace(&self, name: &str) -> Result<()> {
        let mut marketplaces = self.load_known_marketplaces()?;
        if !marketplaces.marketplaces.contains_key(name) {
            return Err(PluginError::MarketplaceNotFound(name.to_string()));
        }

        // Remove directory
        let marketplace_dir = self.paths.global_marketplaces_dir.join(name);
        if marketplace_dir.exists() {
            std::fs::remove_dir_all(&marketplace_dir)?;
        }

        marketplaces.marketplaces.remove(name);
        self.save_known_marketplaces(&marketplaces)?;
        info!(marketplace = name, "Marketplace removed");
        Ok(())
    }

    /// List all registered marketplaces.
    pub fn list_marketplaces(&self) -> Result<Vec<MarketplaceInfo>> {
        let marketplaces = self.load_known_marketplaces()?;
        Ok(marketplaces.marketplaces.into_values().collect())
    }

    /// Sync (git pull) a marketplace.
    pub fn sync_marketplace(&self, name: &str) -> Result<()> {
        let mut marketplaces = self.load_known_marketplaces()?;
        if !marketplaces.marketplaces.contains_key(name) {
            return Err(PluginError::MarketplaceNotFound(name.to_string()));
        }

        let marketplace_dir = self.paths.global_marketplaces_dir.join(name);
        if !marketplace_dir.exists() {
            return Err(PluginError::Other(format!(
                "Marketplace directory missing: {}",
                marketplace_dir.display()
            )));
        }

        self.git_pull(&marketplace_dir)?;

        // Update timestamp
        if let Some(info) = marketplaces.marketplaces.get_mut(name) {
            info.last_updated = Some(Utc::now());
        }
        self.save_known_marketplaces(&marketplaces)?;
        info!(marketplace = name, "Marketplace synced");
        Ok(())
    }

    /// Sync all registered marketplaces. Returns a map of name to optional error message.
    pub fn sync_all_marketplaces(
        &self,
    ) -> Result<std::collections::HashMap<String, Option<String>>> {
        let mut results = std::collections::HashMap::new();
        let marketplaces = self.list_marketplaces()?;
        for m in marketplaces {
            match self.sync_marketplace(&m.name) {
                Ok(()) => {
                    results.insert(m.name, None);
                }
                Err(e) => {
                    results.insert(m.name, Some(e.to_string()));
                }
            }
        }
        Ok(results)
    }

    // ── Catalog ────────────────────────────────────────────────

    /// Get the plugin catalog from a marketplace.
    /// If no marketplace.json exists, auto-discovers plugins from plugins/ and skills/ dirs.
    pub fn get_marketplace_catalog(&self, name: &str) -> Result<MarketplaceCatalog> {
        let marketplaces = self.load_known_marketplaces()?;
        if !marketplaces.marketplaces.contains_key(name) {
            return Err(PluginError::MarketplaceNotFound(name.to_string()));
        }

        let marketplace_dir = self.paths.global_marketplaces_dir.join(name);
        if let Some(catalog_path) = self.get_marketplace_json_path(&marketplace_dir) {
            let content = std::fs::read_to_string(catalog_path)?;
            let catalog: MarketplaceCatalog = serde_json::from_str(&content)?;
            return Ok(catalog);
        }

        // Auto-discover
        Ok(self.auto_discover_catalog(&marketplace_dir))
    }

    /// List all plugins available in a marketplace.
    pub fn list_marketplace_plugins(&self, name: &str) -> Result<Vec<PluginMetadata>> {
        let catalog = self.get_marketplace_catalog(name)?;
        let marketplace_dir = self.paths.global_marketplaces_dir.join(name);
        let mut plugins = Vec::new();

        // Check plugins/ directory
        let plugins_dir = marketplace_dir.join("plugins");
        if plugins_dir.exists() {
            for plugin_name in &catalog.plugins {
                let plugin_dir = plugins_dir.join(plugin_name);
                if plugin_dir.exists() {
                    match self.load_plugin_metadata(&plugin_dir) {
                        Ok(metadata) => plugins.push(metadata),
                        Err(_) => {
                            plugins.push(PluginMetadata {
                                name: plugin_name.clone(),
                                version: "0.0.0".to_string(),
                                description: format!("Plugin: {}", plugin_name),
                                author: None,
                                skills: Self::discover_skills_in_dir(&plugin_dir),
                                repository: None,
                                license: None,
                            });
                        }
                    }
                }
            }
        }

        // Check skills/ directory for auto-discovered catalogs
        let skills_dir = marketplace_dir.join("skills");
        if skills_dir.exists() && catalog.auto_discovered {
            for skill_name in &catalog.plugins {
                let skill_dir = skills_dir.join(skill_name);
                if skill_dir.exists() && skill_dir.join("SKILL.md").exists() {
                    // Skip duplicates
                    if plugins.iter().any(|p| p.name == *skill_name) {
                        continue;
                    }
                    let (_name, desc) = Self::parse_skill_metadata(&skill_dir.join("SKILL.md"));
                    plugins.push(PluginMetadata {
                        name: skill_name.clone(),
                        version: "0.0.0".to_string(),
                        description: if desc.is_empty() {
                            format!("Skill: {}", skill_name)
                        } else {
                            desc
                        },
                        author: None,
                        skills: vec![skill_name.clone()],
                        repository: None,
                        license: None,
                    });
                }
            }
        }

        Ok(plugins)
    }

    /// Search marketplace plugins by query string. Simple substring match on name/description.
    pub fn search_marketplace(
        &self,
        marketplace_name: &str,
        query: &str,
    ) -> Result<Vec<PluginMetadata>> {
        let plugins = self.list_marketplace_plugins(marketplace_name)?;
        let query_lower = query.to_lowercase();
        Ok(plugins
            .into_iter()
            .filter(|p| {
                p.name.to_lowercase().contains(&query_lower)
                    || p.description.to_lowercase().contains(&query_lower)
            })
            .collect())
    }

    // ── Marketplace HTTP fetch (async) ─────────────────────────

    /// Fetch a marketplace catalog from a remote HTTP registry URL.
    pub async fn fetch_remote_catalog(registry_url: &str) -> Result<MarketplaceCatalog> {
        let client = reqwest::Client::new();
        let response = client
            .get(registry_url)
            .header("Accept", "application/json")
            .send()
            .await
            .map_err(|e| PluginError::Other(format!("HTTP request failed: {}", e)))?;

        if !response.status().is_success() {
            return Err(PluginError::Other(format!(
                "Registry returned status {}",
                response.status()
            )));
        }

        let text = response
            .text()
            .await
            .map_err(|e| PluginError::Other(format!("Failed to read response body: {}", e)))?;

        let catalog: MarketplaceCatalog = serde_json::from_str(&text)?;

        Ok(catalog)
    }

    // ── Internal helpers ───────────────────────────────────────

    /// Validate marketplace directory structure.
    fn validate_marketplace(&self, directory: &Path) -> bool {
        // Check for marketplace.json in various locations
        if self.get_marketplace_json_path(directory).is_some() {
            return true;
        }
        // Auto-discovery: accept if plugins/ or skills/ directory exists
        let plugins_dir = directory.join("plugins");
        if plugins_dir.exists() && plugins_dir.is_dir() {
            return true;
        }
        let skills_dir = directory.join("skills");
        if skills_dir.exists() && skills_dir.is_dir() {
            return true;
        }
        false
    }

    /// Find the marketplace.json file in a marketplace directory.
    fn get_marketplace_json_path(&self, directory: &Path) -> Option<std::path::PathBuf> {
        let possible_paths = [
            directory.join(".opendev").join("marketplace.json"),
            directory.join("marketplace.json"),
        ];
        possible_paths.into_iter().find(|p| p.exists())
    }

    /// Auto-discover plugins when no marketplace.json exists.
    fn auto_discover_catalog(&self, marketplace_dir: &Path) -> MarketplaceCatalog {
        let mut plugin_names = Vec::new();

        // Check plugins/ directory
        let plugins_dir = marketplace_dir.join("plugins");
        if plugins_dir.exists()
            && plugins_dir.is_dir()
            && let Ok(entries) = std::fs::read_dir(&plugins_dir)
        {
            for entry in entries.flatten() {
                if entry.path().is_dir()
                    && let Some(name) = entry.file_name().to_str()
                {
                    plugin_names.push(name.to_string());
                }
            }
        }

        // Check skills/ directory
        let skills_dir = marketplace_dir.join("skills");
        if skills_dir.exists()
            && skills_dir.is_dir()
            && let Ok(entries) = std::fs::read_dir(&skills_dir)
        {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.is_dir()
                    && path.join("SKILL.md").exists()
                    && let Some(name) = entry.file_name().to_str()
                {
                    plugin_names.push(name.to_string());
                }
            }
        }

        MarketplaceCatalog {
            plugins: plugin_names,
            auto_discovered: true,
        }
    }

    /// Run `git clone --depth 1` into a target directory.
    fn git_clone(&self, url: &str, branch: &str, target_dir: &Path) -> Result<()> {
        let output = std::process::Command::new("git")
            .args([
                "clone",
                "--depth",
                "1",
                "--branch",
                branch,
                url,
                &target_dir.to_string_lossy(),
            ])
            .output()
            .map_err(|e| PluginError::Git(format!("Failed to run git: {}", e)))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(PluginError::Git(format!("Git clone failed: {}", stderr)));
        }
        Ok(())
    }

    /// Run `git pull` in a directory.
    fn git_pull(&self, dir: &Path) -> Result<()> {
        let output = std::process::Command::new("git")
            .args(["pull"])
            .current_dir(dir)
            .output()
            .map_err(|e| PluginError::Git(format!("Failed to run git: {}", e)))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(PluginError::Git(format!("Git pull failed: {}", stderr)));
        }
        Ok(())
    }
}
