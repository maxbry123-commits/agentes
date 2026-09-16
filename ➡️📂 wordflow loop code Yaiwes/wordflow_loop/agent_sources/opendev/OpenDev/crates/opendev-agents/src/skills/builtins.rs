//! Built-in skills embedded at compile time.

pub(super) struct BuiltinSkill {
    pub filename: &'static str,
    pub content: &'static str,
}

pub(super) const BUILTIN_SKILLS: &[BuiltinSkill] = &[
    BuiltinSkill {
        filename: "commit.md",
        content: include_str!("builtin/commit.md"),
    },
    BuiltinSkill {
        filename: "review-pr.md",
        content: include_str!("builtin/review-pr.md"),
    },
    BuiltinSkill {
        filename: "create-pr.md",
        content: include_str!("builtin/create-pr.md"),
    },
];
