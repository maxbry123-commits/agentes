//! Models.dev API cache and model/provider registry.

mod models;
mod registry;
mod sync;

use std::time::Duration;

pub const MODELS_DEV_URL: &str = "https://models.dev/api.json";
pub const DEFAULT_CACHE_TTL: Duration = Duration::from_secs(60 * 60 * 24); // 24 hours

/// Display order for provider lists.
pub const PRIORITY_PROVIDERS: &[&str] = &[
    "openai",
    "anthropic",
    "fireworks",
    "fireworks-ai",
    "google",
    "deepseek",
    "groq",
    "mistral",
    "cohere",
    "perplexity",
    "togetherai",
    "together",
];

pub use models::{ModelInfo, ProviderInfo, RegistryError};
pub use registry::ModelRegistry;
pub use sync::{is_cache_stale, sync_provider_cache, sync_provider_cache_async};
