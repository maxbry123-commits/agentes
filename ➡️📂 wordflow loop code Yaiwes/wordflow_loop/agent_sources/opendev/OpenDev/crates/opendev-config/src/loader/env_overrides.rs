//! Environment variable overrides for configuration.
//!
//! Applies `OPENDEV_*` environment variables to override loaded config values.

use opendev_models::AppConfig;

use super::ConfigLoader;

impl ConfigLoader {
    /// Apply environment variable overrides.
    pub(super) fn apply_env_overrides(config: &mut AppConfig) {
        Self::apply_env_overrides_with(config, |key| std::env::var(key).ok());
    }

    /// Apply overrides from a variable lookup function.
    ///
    /// Factored out so tests can supply a mock lookup without touching global env.
    pub(super) fn apply_env_overrides_with(
        config: &mut AppConfig,
        get: impl Fn(&str) -> Option<String>,
    ) {
        if let Some(provider) = get("OPENDEV_MODEL_PROVIDER") {
            config.model_provider = provider;
        }
        if let Some(model) = get("OPENDEV_MODEL") {
            config.model = model;
        }
        if let Some(base_url) = get("OPENDEV_API_BASE_URL") {
            config.api_base_url = Some(base_url);
        }
        if let Some(val) = get("OPENDEV_MAX_TOKENS")
            && let Ok(max_tokens) = val.parse()
        {
            config.max_tokens = max_tokens;
        }
        if let Some(val) = get("OPENDEV_TEMPERATURE")
            && let Ok(temp) = val.parse()
        {
            config.temperature = temp;
        }
        if let Some(val) = get("OPENDEV_VERBOSE") {
            config.verbose = val == "1" || val.eq_ignore_ascii_case("true");
        }
        if let Some(val) = get("OPENDEV_DEBUG") {
            config.debug_logging = val == "1" || val.eq_ignore_ascii_case("true");
        }
    }
}
