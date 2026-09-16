//! Configuration and path management for OpenDev.
//!
//! This crate handles:
//! - Hierarchical config loading (project > user > env > defaults)
//! - Path management for all application directories
//! - Model/provider registry with models.dev API cache
//! - Config migration (versioned configs with automatic upgrade)
//! - Environment-specific profiles (dev, prod, fast)
//! - Poll-based config file watcher for hot-reload

pub mod loader;
pub mod migration;
pub mod models_dev;
pub mod paths;
pub mod profile;
pub mod watcher;

pub use loader::ConfigLoader;
pub use migration::{CURRENT_CONFIG_VERSION, config_version, migrate_config, needs_migration};
pub use models_dev::{ModelInfo, ModelRegistry, ProviderInfo, sync_provider_cache_async};
pub use paths::Paths;
pub use profile::{Profile, apply_profile};
pub use watcher::ConfigWatcher;
