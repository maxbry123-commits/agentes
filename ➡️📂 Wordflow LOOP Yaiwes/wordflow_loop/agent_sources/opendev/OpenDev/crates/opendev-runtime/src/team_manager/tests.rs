use tempfile::TempDir;

use super::*;

fn temp_teams_dir() -> TempDir {
    TempDir::new().unwrap()
}

#[test]
fn test_create_and_get_team() {
    let dir = temp_teams_dir();
    let tm = TeamManager::new(dir.path().canonicalize().unwrap());

    let config = tm.create_team("alpha", "leader", "sess-1").unwrap();
    assert_eq!(config.name, "alpha");
    assert_eq!(config.leader, "leader");
    assert!(config.members.is_empty());

    let retrieved = tm.get_team("alpha").unwrap();
    assert_eq!(retrieved.name, "alpha");
}

#[test]
fn test_add_member() {
    let dir = temp_teams_dir();
    let tm = TeamManager::new(dir.path().canonicalize().unwrap());

    tm.create_team("alpha", "leader", "sess-1").unwrap();
    tm.add_member(
        "alpha",
        TeamMember {
            name: "researcher".into(),
            agent_type: "Explore".into(),
            task_id: "t1".into(),
            task: "explore the codebase".into(),
            status: TeamMemberStatus::Busy,
            joined_at_ms: now_ms(),
        },
    )
    .unwrap();

    let config = tm.get_team("alpha").unwrap();
    assert_eq!(config.members.len(), 1);
    assert_eq!(config.members[0].name, "researcher");
}

#[test]
fn test_delete_team_cleans_files() {
    let dir = temp_teams_dir();
    let teams_dir = dir.path().canonicalize().unwrap();
    let tm = TeamManager::new(teams_dir.clone());

    tm.create_team("alpha", "leader", "sess-1").unwrap();
    assert!(teams_dir.join("alpha/team.json").exists());

    tm.delete_team("alpha").unwrap();
    assert!(!teams_dir.join("alpha").exists());
    assert!(tm.get_team("alpha").is_none());
}

#[test]
fn test_list_teams() {
    let dir = temp_teams_dir();
    let tm = TeamManager::new(dir.path().canonicalize().unwrap());

    tm.create_team("alpha", "leader", "sess-1").unwrap();
    tm.create_team("beta", "leader", "sess-1").unwrap();

    let teams = tm.list_teams();
    assert_eq!(teams.len(), 2);
}

#[test]
fn test_update_member_status() {
    let dir = temp_teams_dir();
    let tm = TeamManager::new(dir.path().canonicalize().unwrap());

    tm.create_team("alpha", "leader", "sess-1").unwrap();
    tm.add_member(
        "alpha",
        TeamMember {
            name: "worker".into(),
            agent_type: "Explore".into(),
            task_id: "t1".into(),
            task: "do work".into(),
            status: TeamMemberStatus::Busy,
            joined_at_ms: now_ms(),
        },
    )
    .unwrap();

    tm.update_member_status("alpha", "worker", TeamMemberStatus::Done);
    let config = tm.get_team("alpha").unwrap();
    assert_eq!(config.members[0].status, TeamMemberStatus::Done);
}

#[test]
fn test_team_dir_path() {
    let dir = temp_teams_dir();
    let teams_dir = dir.path().canonicalize().unwrap();
    let tm = TeamManager::new(teams_dir.clone());

    assert_eq!(tm.team_dir("alpha"), teams_dir.join("alpha"));
}

#[test]
fn test_get_nonexistent_team() {
    let dir = temp_teams_dir();
    let tm = TeamManager::new(dir.path().canonicalize().unwrap());
    assert!(tm.get_team("nope").is_none());
}

#[test]
fn test_team_persisted_to_disk() {
    let dir = temp_teams_dir();
    let teams_dir = dir.path().canonicalize().unwrap();
    let tm = TeamManager::new(teams_dir.clone());

    tm.create_team("alpha", "leader", "sess-1").unwrap();
    tm.add_member(
        "alpha",
        TeamMember {
            name: "w1".into(),
            agent_type: "Explore".into(),
            task_id: "t1".into(),
            task: "explore".into(),
            status: TeamMemberStatus::Idle,
            joined_at_ms: now_ms(),
        },
    )
    .unwrap();

    // Read from disk directly
    let content = fs::read_to_string(teams_dir.join("alpha/team.json")).unwrap();
    let config: TeamConfig = serde_json::from_str(&content).unwrap();
    assert_eq!(config.members.len(), 1);
    assert_eq!(config.members[0].name, "w1");
}
