//! Git worktree manager for agent isolation.
//!
//! Creates isolated git worktrees so agents can edit files without
//! affecting the main working directory. Each agent gets its own branch
//! and worktree path.

use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

use tracing::{info, warn};

/// Result of merging a worktree branch back.
#[derive(Debug)]
pub enum MergeResult {
    /// Merge completed cleanly.
    Clean,
    /// Merge had conflicts.
    Conflict { files: Vec<String> },
    /// No changes were made in the worktree.
    NoChanges,
}

/// Information about a created worktree.
#[derive(Debug, Clone)]
pub struct WorktreeInfo {
    pub path: PathBuf,
    pub branch: String,
    pub agent_id: String,
}

/// Manages git worktrees for agent isolation.
pub struct WorktreeManager {
    base_dir: PathBuf,
}

impl WorktreeManager {
    /// Create a new worktree manager.
    ///
    /// `base_dir` is typically `{repo_root}/.opendev/worktrees/`.
    pub fn new(base_dir: PathBuf) -> Self {
        Self { base_dir }
    }

    /// Create an isolated worktree for an agent.
    pub fn create(&self, repo_root: &Path, agent_id: &str) -> std::io::Result<WorktreeInfo> {
        let short_id = &agent_id[..8.min(agent_id.len())];
        let branch_name = format!("opendev/agent-{short_id}");
        let worktree_path = self.base_dir.join(short_id);

        fs::create_dir_all(&self.base_dir)?;

        // Create the worktree with a new branch from HEAD
        let output = Command::new("git")
            .args(["worktree", "add", "-b", &branch_name])
            .arg(&worktree_path)
            .current_dir(repo_root)
            .output()?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            // If branch already exists, try without -b
            if stderr.contains("already exists") {
                let output2 = Command::new("git")
                    .args(["worktree", "add"])
                    .arg(&worktree_path)
                    .arg(&branch_name)
                    .current_dir(repo_root)
                    .output()?;
                if !output2.status.success() {
                    return Err(std::io::Error::other(format!(
                        "Failed to create worktree: {}",
                        String::from_utf8_lossy(&output2.stderr)
                    )));
                }
            } else {
                return Err(std::io::Error::other(format!(
                    "Failed to create worktree: {stderr}"
                )));
            }
        }

        info!(
            agent_id = %agent_id,
            branch = %branch_name,
            path = %worktree_path.display(),
            "Created git worktree"
        );

        Ok(WorktreeInfo {
            path: worktree_path,
            branch: branch_name,
            agent_id: agent_id.to_string(),
        })
    }

    /// Check if an agent made any changes in their worktree.
    pub fn has_changes(&self, agent_id: &str, _repo_root: &Path) -> bool {
        let short_id = &agent_id[..8.min(agent_id.len())];
        let worktree_path = self.base_dir.join(short_id);

        let output = Command::new("git")
            .args(["status", "--porcelain"])
            .current_dir(&worktree_path)
            .output();

        match output {
            Ok(o) => !o.stdout.is_empty(),
            Err(_) => false,
        }
    }

    /// Clean up a worktree after an agent completes.
    ///
    /// If no changes were made, removes the worktree and branch.
    /// If changes exist, keeps the worktree for manual review.
    pub fn cleanup(
        &self,
        agent_id: &str,
        repo_root: &Path,
        has_changes: bool,
    ) -> std::io::Result<()> {
        let short_id = &agent_id[..8.min(agent_id.len())];
        let worktree_path = self.base_dir.join(short_id);
        let branch_name = format!("opendev/agent-{short_id}");

        if has_changes {
            info!(
                agent_id = %agent_id,
                path = %worktree_path.display(),
                "Keeping worktree with changes for review"
            );
            return Ok(());
        }

        // Remove worktree
        let output = Command::new("git")
            .args(["worktree", "remove", "--force"])
            .arg(&worktree_path)
            .current_dir(repo_root)
            .output()?;

        if !output.status.success() {
            warn!(
                agent_id = %agent_id,
                stderr = %String::from_utf8_lossy(&output.stderr),
                "Failed to remove worktree, cleaning up manually"
            );
            let _ = fs::remove_dir_all(&worktree_path);
        }

        // Delete the branch
        let _ = Command::new("git")
            .args(["branch", "-D", &branch_name])
            .current_dir(repo_root)
            .output();

        info!(agent_id = %agent_id, "Cleaned up worktree");
        Ok(())
    }

    /// List existing worktrees.
    pub fn list(&self) -> Vec<WorktreeInfo> {
        let mut infos = Vec::new();
        if let Ok(entries) = fs::read_dir(&self.base_dir) {
            for entry in entries.flatten() {
                if entry.path().is_dir() {
                    let name = entry.file_name().to_string_lossy().to_string();
                    infos.push(WorktreeInfo {
                        path: entry.path(),
                        branch: format!("opendev/agent-{name}"),
                        agent_id: name,
                    });
                }
            }
        }
        infos
    }
}

impl std::fmt::Debug for WorktreeManager {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("WorktreeManager")
            .field("base_dir", &self.base_dir)
            .finish()
    }
}

#[cfg(test)]
#[path = "tests.rs"]
mod tests;
