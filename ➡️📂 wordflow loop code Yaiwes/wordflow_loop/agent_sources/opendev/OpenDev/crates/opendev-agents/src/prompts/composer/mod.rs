//! Prompt composition engine with conditional loading and section caching.
//!
//! Composes system prompts from modular sections based on runtime context
//! and conversation lifecycle. Supports priority ordering, conditional
//! inclusion, cache-aware two-part splitting, and variable substitution.
//!
//! Follows Claude Code's pattern of per-turn composition with a section
//! cache: `Static` and `Cached` sections are resolved once and reused,
//! while `Uncached` sections recompute every turn.
//!
//! Templates are resolved in order:
//! 1. Content provider closure (if set) — for dynamic runtime content
//! 2. Embedded (compile-time `include_str!`) — zero filesystem dependency
//! 3. Filesystem fallback (`templates_dir`) — for user customisation

mod conditions;
mod factories;

use regex::Regex;
use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::LazyLock;

use super::embedded;

// Re-export public items from submodules
pub use conditions::{ctx_bool, ctx_eq, ctx_in, ctx_present};
pub use factories::{create_composer, create_default_composer};

/// Regex to strip HTML comment frontmatter from markdown files.
static FRONTMATTER_RE: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?s)^\s*<!--.*?-->\s*").expect("valid regex: frontmatter pattern")
});

/// Regex for `{{variable_name}}` placeholders in templates.
static VARIABLE_RE: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"\{\{(\w+)\}\}").expect("valid regex: variable placeholder pattern")
});

/// Runtime context passed to condition functions for section filtering.
pub type PromptContext = HashMap<String, serde_json::Value>;

/// A condition function that determines if a section should be included.
pub type ConditionFn = Box<dyn Fn(&PromptContext) -> bool + Send + Sync>;

/// A closure that dynamically generates section content at compose time.
pub type ContentProviderFn = Box<dyn Fn() -> Option<String> + Send + Sync>;

/// Cache policy for a prompt section, modelled after Claude Code's
/// `systemPromptSection` vs `DANGEROUS_uncachedSystemPromptSection`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CachePolicy {
    /// Stable across the entire session. Cached until explicit `clear_all_cache()`.
    /// Used for: identity, policies, tool guidance, code quality rules.
    Static,
    /// Session-specific but stable across turns. Cached until `clear_cache()`
    /// (triggered by `/compact`, `/clear`).
    /// Used for: memory, environment context, scratchpad.
    Cached,
    /// Recomputed every turn. Never served from cache.
    /// Used for: MCP instructions (servers connect/disconnect between turns).
    Uncached,
}

/// A section to conditionally include in the system prompt.
pub struct PromptSection {
    /// Section identifier.
    pub name: String,
    /// Path to template file (relative to templates_dir). Ignored when
    /// `content_provider` is set.
    pub file_path: String,
    /// Optional predicate to determine if section should be included.
    pub condition: Option<ConditionFn>,
    /// Loading priority (lower = earlier in prompt).
    pub priority: i32,
    /// Cache policy controlling when this section is recomputed.
    pub cache_policy: CachePolicy,
    /// Optional closure that generates content dynamically instead of
    /// loading from a template file.
    pub content_provider: Option<ContentProviderFn>,
}

impl std::fmt::Debug for PromptSection {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("PromptSection")
            .field("name", &self.name)
            .field("file_path", &self.file_path)
            .field("priority", &self.priority)
            .field("cache_policy", &self.cache_policy)
            .field("has_condition", &self.condition.is_some())
            .field("has_content_provider", &self.content_provider.is_some())
            .finish()
    }
}

/// Composes system prompts from modular sections with per-turn caching.
///
/// Follows Claude Code's approach of building prompts from many small
/// markdown files with conditional loading based on runtime context.
/// Sections are cached according to their [`CachePolicy`]:
/// - `Static`: resolved once, cached for the session
/// - `Cached`: resolved once, cleared on `/compact` or `/clear`
/// - `Uncached`: resolved fresh every `compose()` call
///
/// Templates are resolved first from content providers (dynamic), then
/// the embedded store (compile-time), then the filesystem `templates_dir`.
pub struct PromptComposer {
    templates_dir: PathBuf,
    sections: Vec<PromptSection>,
    /// Per-section content cache. Keyed by section name.
    section_cache: HashMap<String, Option<String>>,
    /// Pre-resolved overrides injected by callers before `compose()`.
    /// Used for async content (e.g. MCP) that must be resolved outside
    /// the composer's synchronous `compose()` path.
    section_overrides: HashMap<String, Option<String>>,
}

impl std::fmt::Debug for PromptComposer {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("PromptComposer")
            .field("templates_dir", &self.templates_dir)
            .field("sections", &self.sections)
            .field("cache_entries", &self.section_cache.len())
            .field("override_entries", &self.section_overrides.len())
            .finish()
    }
}

impl PromptComposer {
    /// Create a new composer.
    pub fn new(templates_dir: impl Into<PathBuf>) -> Self {
        Self {
            templates_dir: templates_dir.into(),
            sections: Vec::new(),
            section_cache: HashMap::new(),
            section_overrides: HashMap::new(),
        }
    }

    /// Register a prompt section for conditional inclusion.
    ///
    /// The `cacheable` parameter maps to [`CachePolicy`]:
    /// - `true` → `Static` (cached for the session)
    /// - `false` → `Uncached` (recomputed every turn)
    pub fn register_section(
        &mut self,
        name: impl Into<String>,
        file_path: impl Into<String>,
        condition: Option<ConditionFn>,
        priority: i32,
        cacheable: bool,
    ) {
        self.sections.push(PromptSection {
            name: name.into(),
            file_path: file_path.into(),
            condition,
            priority,
            cache_policy: if cacheable {
                CachePolicy::Static
            } else {
                CachePolicy::Uncached
            },
            content_provider: None,
        });
    }

    /// Register a section with an explicit [`CachePolicy`].
    pub fn register_section_with_policy(
        &mut self,
        name: impl Into<String>,
        file_path: impl Into<String>,
        condition: Option<ConditionFn>,
        priority: i32,
        cache_policy: CachePolicy,
    ) {
        self.sections.push(PromptSection {
            name: name.into(),
            file_path: file_path.into(),
            condition,
            priority,
            cache_policy,
            content_provider: None,
        });
    }

    /// Register a dynamic section with a content provider closure.
    ///
    /// The content provider replaces template loading — the `file_path` is
    /// set to an empty string and ignored.
    pub fn register_dynamic_section(
        &mut self,
        name: impl Into<String>,
        cache_policy: CachePolicy,
        priority: i32,
        condition: Option<ConditionFn>,
        content_provider: ContentProviderFn,
    ) {
        self.sections.push(PromptSection {
            name: name.into(),
            file_path: String::new(),
            condition,
            priority,
            cache_policy,
            content_provider: Some(content_provider),
        });
    }

    /// Register a section with defaults (priority=50, Static, no condition).
    pub fn register_simple(&mut self, name: impl Into<String>, file_path: impl Into<String>) {
        self.register_section(name, file_path, None, 50, true);
    }

    /// Inject a pre-resolved value for a section, bypassing its normal
    /// content resolution. Used for async content (e.g. MCP instructions)
    /// that must be resolved outside the synchronous `compose()` path.
    ///
    /// The override is consumed on the next `compose()` call and does NOT
    /// persist in the section cache (caching follows normal policy after).
    pub fn set_section_override(&mut self, name: impl Into<String>, value: Option<String>) {
        self.section_overrides.insert(name.into(), value);
    }

    /// Compose final prompt from registered sections.
    ///
    /// Sections are filtered by condition, sorted by priority, resolved
    /// (cache → override → provider → embedded → filesystem), and joined.
    pub fn compose(&mut self, context: &PromptContext) -> String {
        let indices = self.filtered_sorted_indices(context);
        let parts: Vec<String> = indices
            .into_iter()
            .filter_map(|i| self.resolve_section_at(i))
            .collect();
        self.section_overrides.clear();
        parts.join("\n\n")
    }

    /// Compose final prompt with variable substitution.
    pub fn compose_with_vars(
        &mut self,
        context: &PromptContext,
        variables: &HashMap<String, String>,
    ) -> String {
        let raw = self.compose(context);
        substitute_variables(&raw, variables)
    }

    /// Compose prompt split into stable (cacheable) and dynamic parts.
    ///
    /// For Anthropic prompt caching: the stable part gets cache_control,
    /// the dynamic part changes per session/turn.
    /// - Stable = `Static` + `Cached` sections
    /// - Dynamic = `Uncached` sections
    pub fn compose_two_part(&mut self, context: &PromptContext) -> (String, String) {
        let indices = self.filtered_sorted_indices(context);
        let mut stable_parts = Vec::new();
        let mut dynamic_parts = Vec::new();

        for i in indices {
            let cache_policy = self.sections[i].cache_policy;
            if let Some(content) = self.resolve_section_at(i) {
                match cache_policy {
                    CachePolicy::Static | CachePolicy::Cached => {
                        stable_parts.push(content);
                    }
                    CachePolicy::Uncached => {
                        dynamic_parts.push(content);
                    }
                }
            }
        }

        self.section_overrides.clear();
        (stable_parts.join("\n\n"), dynamic_parts.join("\n\n"))
    }

    /// Compose two-part prompt with variable substitution on both halves.
    pub fn compose_two_part_with_vars(
        &mut self,
        context: &PromptContext,
        variables: &HashMap<String, String>,
    ) -> (String, String) {
        let (stable, dynamic) = self.compose_two_part(context);
        (
            substitute_variables(&stable, variables),
            substitute_variables(&dynamic, variables),
        )
    }

    /// Get the number of registered sections.
    pub fn section_count(&self) -> usize {
        self.sections.len()
    }

    /// Get names of all registered sections.
    pub fn section_names(&self) -> Vec<&str> {
        self.sections.iter().map(|s| s.name.as_str()).collect()
    }

    /// Clear `Cached` section entries. Called on `/compact` and `/clear`.
    ///
    /// `Static` entries survive — they are stable for the entire session.
    pub fn clear_cache(&mut self) {
        let cached_names: Vec<String> = self
            .sections
            .iter()
            .filter(|s| s.cache_policy == CachePolicy::Cached)
            .map(|s| s.name.clone())
            .collect();
        for name in cached_names {
            self.section_cache.remove(&name);
        }
    }

    /// Clear all cache entries including `Static`. Called on session switch.
    pub fn clear_all_cache(&mut self) {
        self.section_cache.clear();
    }

    /// Return indices of included sections, sorted by priority.
    fn filtered_sorted_indices(&self, context: &PromptContext) -> Vec<usize> {
        let mut indices: Vec<usize> = self
            .sections
            .iter()
            .enumerate()
            .filter(|(_, s)| s.condition.as_ref().is_none_or(|f| f(context)))
            .map(|(i, _)| i)
            .collect();
        indices.sort_by_key(|&i| self.sections[i].priority);
        indices
    }

    /// Resolve a section's content by index, using the caching pipeline:
    /// 1. For `Static`/`Cached`: return cached value if present
    /// 2. Check overrides (pre-resolved async content)
    /// 3. Call content_provider if set
    /// 4. Load from embedded templates
    /// 5. Fallback to filesystem
    /// 6. Store result in cache (for `Static`/`Cached`)
    fn resolve_section_at(&mut self, index: usize) -> Option<String> {
        let section = &self.sections[index];
        let name = section.name.clone();
        let cache_policy = section.cache_policy;

        // For Static/Cached, try the cache first
        if cache_policy != CachePolicy::Uncached
            && let Some(cached) = self.section_cache.get(&name)
        {
            return cached.clone();
        }

        // Check for pre-resolved override
        let content = if let Some(override_val) = self.section_overrides.get(&name) {
            override_val.clone()
        } else {
            self.load_section_content(&self.sections[index])
        };

        // Cache the result for Static and Cached policies
        if cache_policy != CachePolicy::Uncached {
            self.section_cache.insert(name, content.clone());
        }

        content
    }

    /// Load a section's content: try provider, then embedded, then filesystem.
    fn load_section_content(&self, section: &PromptSection) -> Option<String> {
        // 1. Try content provider
        if let Some(ref provider) = section.content_provider {
            return provider();
        }

        // 2. Try embedded templates
        if let Some(raw) = embedded::get_embedded(&section.file_path) {
            let stripped = strip_frontmatter(raw);
            if !stripped.is_empty() {
                return Some(stripped);
            }
        }

        // 3. Fallback to filesystem
        let file_path = self.templates_dir.join(&section.file_path);
        if !file_path.exists() {
            return None;
        }
        let content = std::fs::read_to_string(&file_path).ok()?;
        let stripped = strip_frontmatter(&content);
        if stripped.is_empty() {
            None
        } else {
            Some(stripped)
        }
    }
}

// ---------------------------------------------------------------------------
// Utility functions
// ---------------------------------------------------------------------------

/// Strip HTML comment frontmatter from markdown content.
pub fn strip_frontmatter(content: &str) -> String {
    FRONTMATTER_RE.replace(content, "").trim().to_string()
}

/// Substitute `{{variable_name}}` placeholders in a template string.
///
/// Variables not present in the map are left as-is.
///
/// ```
/// use std::collections::HashMap;
/// use opendev_agents::prompts::substitute_variables;
///
/// let mut vars = HashMap::new();
/// vars.insert("session_id".into(), "abc-123".into());
/// let result = substitute_variables("path: ~/.opendev/sessions/{{session_id}}/", &vars);
/// assert_eq!(result, "path: ~/.opendev/sessions/abc-123/");
/// ```
pub fn substitute_variables(template: &str, variables: &HashMap<String, String>) -> String {
    VARIABLE_RE
        .replace_all(template, |caps: &regex::Captures| {
            let key = &caps[1];
            variables
                .get(key)
                .cloned()
                .unwrap_or_else(|| caps[0].to_string())
        })
        .into_owned()
}

#[cfg(test)]
mod tests;
