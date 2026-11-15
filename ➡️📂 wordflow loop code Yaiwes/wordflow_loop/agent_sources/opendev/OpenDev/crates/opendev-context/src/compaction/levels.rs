//! Optimization levels for staged context compaction.

/// Optimization level returned by `check_usage`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OptimizationLevel {
    /// No optimization needed.
    None,
    /// 70%: Warning logged, tracking begins.
    Warning,
    /// 80%: Progressive observation masking.
    Mask,
    /// 85%: Fast pruning of old tool outputs.
    Prune,
    /// 90%: Aggressive masking + trimming.
    Aggressive,
    /// 99%: Full LLM-powered compaction.
    Compact,
}

impl OptimizationLevel {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::None => "none",
            Self::Warning => "warning",
            Self::Mask => "mask",
            Self::Prune => "prune",
            Self::Aggressive => "aggressive",
            Self::Compact => "compact",
        }
    }
}
