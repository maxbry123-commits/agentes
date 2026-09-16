//! Data models for the plugin system.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

/// Source of a plugin installation.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum PluginSource {
    /// Installed from a git repository.
    Git { url: String, branch: String },
    /// Installed from a local directory.
    Local { path: PathBuf },
    /// Installed from a marketplace.
    Marketplace { marketplace: String },
}

/// Status of a plugin.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum PluginStatus {
    /// Plugin is installed and active.
    Installed,
    /// Plugin is installed but disabled.
    Disabled,
    /// Plugin encountered an error.
    Error(String),
}

/// Installation scope for plugins.
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum PluginScope {
    /// User-global plugins (~/.opendev/plugins/).
    User,
    /// Project-local plugins (.opendev/plugins/).
    Project,
}

/// A tool definition within a plugin manifest.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ToolDefinition {
    /// Tool name.
    pub name: String,
    /// Tool description.
    #[serde(default)]
    pub description: String,
    /// JSON schema for tool parameters.
    #[serde(default)]
    pub parameters: serde_json::Value,
}

/// A prompt template within a plugin manifest.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PromptTemplate {
    /// Prompt name/identifier.
    pub name: String,
    /// Prompt description.
    #[serde(default)]
    pub description: String,
    /// The template content.
    #[serde(default)]
    pub template: String,
}

/// Plugin manifest loaded from `manifest.json`.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PluginManifest {
    /// Plugin name.
    pub name: String,
    /// Plugin version (semver).
    pub version: String,
    /// Plugin description.
    #[serde(default)]
    pub description: String,
    /// Plugin author.
    #[serde(default)]
    pub author: Option<String>,
    /// Tool definitions provided by the plugin.
    #[serde(default)]
    pub tools: Vec<ToolDefinition>,
    /// Prompt templates provided by the plugin.
    #[serde(default)]
    pub prompts: Vec<PromptTemplate>,
    /// Plugin dependencies (other plugin names).
    #[serde(default)]
    pub dependencies: Vec<String>,
    /// Skills provided by the plugin.
    #[serde(default)]
    pub skills: Vec<String>,
    /// Source repository URL.
    #[serde(default)]
    pub repository: Option<String>,
    /// License identifier.
    #[serde(default)]
    pub license: Option<String>,
}

/// Configuration for a single installed plugin.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PluginConfig {
    /// Plugin name.
    pub name: String,
    /// Installed version.
    pub version: String,
    /// Installation source.
    pub source: PluginSource,
    /// Current status.
    pub status: PluginStatus,
    /// Installation scope.
    pub scope: PluginScope,
    /// Whether the plugin is enabled.
    pub enabled: bool,
    /// Path to the installed plugin directory.
    pub path: PathBuf,
    /// When the plugin was installed.
    pub installed_at: DateTime<Utc>,
    /// Marketplace this plugin came from (if applicable).
    #[serde(default)]
    pub marketplace: Option<String>,
}

/// Information about a registered marketplace.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketplaceInfo {
    /// Unique name for this marketplace.
    pub name: String,
    /// Git URL of the marketplace repository.
    pub url: String,
    /// Git branch to track.
    #[serde(default = "default_branch")]
    pub branch: String,
    /// When this marketplace was added.
    pub added_at: DateTime<Utc>,
    /// Last time marketplace was synced.
    #[serde(default)]
    pub last_updated: Option<DateTime<Utc>>,
}

fn default_branch() -> String {
    "main".to_string()
}

/// Registry of known marketplaces.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct KnownMarketplaces {
    /// Map of marketplace name to info.
    #[serde(default)]
    pub marketplaces: HashMap<String, MarketplaceInfo>,
}

/// Registry of installed plugins.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct InstalledPlugins {
    /// Map of "marketplace:plugin" key to plugin config.
    #[serde(default)]
    pub plugins: HashMap<String, PluginConfig>,
}

impl InstalledPlugins {
    /// Generate registry key for a plugin.
    pub fn make_key(marketplace: &str, plugin: &str) -> String {
        format!("{}:{}", marketplace, plugin)
    }

    /// Add a plugin to the registry.
    pub fn add(&mut self, plugin: PluginConfig) {
        let key = Self::make_key(
            plugin.marketplace.as_deref().unwrap_or("local"),
            &plugin.name,
        );
        self.plugins.insert(key, plugin);
    }

    /// Remove a plugin from the registry.
    pub fn remove(&mut self, marketplace: &str, plugin: &str) -> Option<PluginConfig> {
        let key = Self::make_key(marketplace, plugin);
        self.plugins.remove(&key)
    }

    /// Get a plugin from the registry.
    pub fn get(&self, marketplace: &str, plugin: &str) -> Option<&PluginConfig> {
        let key = Self::make_key(marketplace, plugin);
        self.plugins.get(&key)
    }

    /// Get a mutable reference to a plugin.
    pub fn get_mut(&mut self, marketplace: &str, plugin: &str) -> Option<&mut PluginConfig> {
        let key = Self::make_key(marketplace, plugin);
        self.plugins.get_mut(&key)
    }
}

/// Marketplace plugin catalog.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct MarketplaceCatalog {
    /// List of plugin names available.
    #[serde(default)]
    pub plugins: Vec<String>,
    /// Whether catalog was auto-discovered (no marketplace.json).
    #[serde(default)]
    pub auto_discovered: bool,
}

/// Plugin metadata from plugin.json or marketplace listing.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PluginMetadata {
    /// Plugin name.
    pub name: String,
    /// Plugin version.
    pub version: String,
    /// Plugin description.
    #[serde(default)]
    pub description: String,
    /// Plugin author.
    #[serde(default)]
    pub author: Option<String>,
    /// Skills provided by the plugin.
    #[serde(default)]
    pub skills: Vec<String>,
    /// Source repository URL.
    #[serde(default)]
    pub repository: Option<String>,
    /// License identifier.
    #[serde(default)]
    pub license: Option<String>,
}
