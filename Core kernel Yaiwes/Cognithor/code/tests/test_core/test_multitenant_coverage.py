"""Coverage-Tests fuer multitenant.py -- TenantManager, TrustNegotiator, EmergencyController."""

from __future__ import annotations

from cognithor.core.multitenant import (
    EmergencyAction,
    EmergencyController,
    EmergencyEvent,
    MultiTenantGovernor,
    Tenant,
    TenantManager,
    TenantPlan,
    TenantStatus,
    TenantUser,
    TrustLevel,
    TrustNegotiator,
    TrustPolicy,
    TrustRelation,
)

# ============================================================================
# TenantUser
# ============================================================================


class TestTenantUser:
    def test_to_dict(self) -> None:
        user = TenantUser(user_id="u1", name="Alice", email="a@b.com", role="admin")
        d = user.to_dict()
        assert d["user_id"] == "u1"
        assert d["role"] == "admin"


# ============================================================================
# Tenant
# ============================================================================


class TestTenant:
    def test_properties(self) -> None:
        t = Tenant(tenant_id="abc123", name="Test Tenant")
        assert "abc123" in t.data_path
        assert "abc123" in t.secrets_path
        assert "abc123" in t.db_name

    def test_limits(self) -> None:
        t = Tenant(tenant_id="x", name="X", plan=TenantPlan.FREE)
        assert t.limits["max_agents"] == 1

    def test_can_add_agent(self) -> None:
        t = Tenant(tenant_id="x", name="X", plan=TenantPlan.FREE)
        assert t.can_add_agent(0) is True
        assert t.can_add_agent(1) is False

    def test_can_add_agent_enterprise(self) -> None:
        t = Tenant(tenant_id="x", name="X", plan=TenantPlan.ENTERPRISE)
        assert t.can_add_agent(999) is True  # Unlimited

    def test_can_add_user(self) -> None:
        t = Tenant(tenant_id="x", name="X", plan=TenantPlan.FREE)
        assert t.can_add_user() is True
        t.users.append(TenantUser(user_id="u1", name="A", email="a@b.com"))
        assert t.can_add_user() is False

    def test_can_add_user_enterprise(self) -> None:
        t = Tenant(tenant_id="x", name="X", plan=TenantPlan.ENTERPRISE)
        assert t.can_add_user() is True

    def test_to_dict(self) -> None:
        t = Tenant(tenant_id="abc", name="Test")
        d = t.to_dict()
        assert d["tenant_id"] == "abc"
        assert d["plan"] == "free"
        assert d["status"] == "active"


# ============================================================================
# TenantManager
# ============================================================================


class TestTenantManager:
    def test_create_tenant(self) -> None:
        tm = TenantManager()
        t = tm.create("Test Corp", "admin@test.com", TenantPlan.STARTER)
        assert t.name == "Test Corp"
        assert t.plan == TenantPlan.STARTER
        assert len(t.users) == 1
        assert t.users[0].role == "admin"

    def test_get_tenant(self) -> None:
        tm = TenantManager()
        t = tm.create("Test", "a@b.com")
        found = tm.get(t.tenant_id)
        assert found is t

    def test_get_nonexistent(self) -> None:
        tm = TenantManager()
        assert tm.get("nonexistent") is None

    def test_find_by_email(self) -> None:
        tm = TenantManager()
        tm.create("Corp A", "alice@corp.com")
        tm.create("Corp B", "bob@corp.com")
        results = tm.find_by_email("alice@corp.com")
        assert len(results) == 1

    def test_find_by_email_as_user(self) -> None:
        tm = TenantManager()
        t = tm.create("Corp", "admin@corp.com", TenantPlan.STARTER)  # 5 users max
        tm.add_user(
            t.tenant_id,
            TenantUser(
                user_id="u2",
                name="Bob",
                email="bob@corp.com",
                role="user",
            ),
        )
        results = tm.find_by_email("bob@corp.com")
        assert len(results) == 1

    def test_suspend_and_activate(self) -> None:
        tm = TenantManager()
        t = tm.create("Test", "a@b.com")
        assert tm.suspend(t.tenant_id) is True
        assert t.status == TenantStatus.SUSPENDED
        assert tm.activate(t.tenant_id) is True
        assert t.status == TenantStatus.ACTIVE

    def test_suspend_nonexistent(self) -> None:
        tm = TenantManager()
        assert tm.suspend("x") is False
        assert tm.activate("x") is False

    def test_upgrade(self) -> None:
        tm = TenantManager()
        t = tm.create("Test", "a@b.com")
        assert tm.upgrade(t.tenant_id, TenantPlan.PROFESSIONAL) is True
        assert t.plan == TenantPlan.PROFESSIONAL

    def test_upgrade_nonexistent(self) -> None:
        tm = TenantManager()
        assert tm.upgrade("x", TenantPlan.ENTERPRISE) is False

    def test_add_user(self) -> None:
        tm = TenantManager()
        t = tm.create("Test", "a@b.com", TenantPlan.STARTER)
        user = TenantUser(user_id="u2", name="Bob", email="bob@b.com")
        assert tm.add_user(t.tenant_id, user) is True

    def test_add_user_over_limit(self) -> None:
        tm = TenantManager()
        t = tm.create("Test", "a@b.com", TenantPlan.FREE)
        # FREE plan allows 1 user, already has admin
        user = TenantUser(user_id="u2", name="Bob", email="bob@b.com")
        assert tm.add_user(t.tenant_id, user) is False

    def test_add_user_nonexistent(self) -> None:
        tm = TenantManager()
        user = TenantUser(user_id="u1", name="A", email="a@b.com")
        assert tm.add_user("nonexistent", user) is False

    def test_remove_user(self) -> None:
        tm = TenantManager()
        t = tm.create("Test", "a@b.com", TenantPlan.STARTER)
        user = TenantUser(user_id="u2", name="Bob", email="bob@b.com")
        tm.add_user(t.tenant_id, user)
        assert tm.remove_user(t.tenant_id, "u2") is True
        assert tm.remove_user(t.tenant_id, "u2") is False  # Already removed

    def test_remove_user_nonexistent_tenant(self) -> None:
        tm = TenantManager()
        assert tm.remove_user("x", "u1") is False

    def test_active_tenants(self) -> None:
        tm = TenantManager()
        tm.create("A", "a@b.com")
        t2 = tm.create("B", "b@b.com")
        tm.suspend(t2.tenant_id)
        assert len(tm.active_tenants()) == 1

    def test_tenant_count(self) -> None:
        tm = TenantManager()
        assert tm.tenant_count == 0
        tm.create("A", "a@b.com")
        assert tm.tenant_count == 1

    def test_stats(self) -> None:
        tm = TenantManager()
        tm.create("A", "a@b.com")
        stats = tm.stats()
        assert stats["total_tenants"] == 1
        assert stats["active"] == 1


# ============================================================================
# TrustPolicy / TrustRelation
# ============================================================================


class TestTrustPolicy:
    def test_defaults(self) -> None:
        p = TrustPolicy(policy_id="default")
        assert p.min_trust_for_delegation == TrustLevel.VERIFIED
        assert p.require_mutual_auth is True

    def test_to_dict(self) -> None:
        p = TrustPolicy(policy_id="test")
        d = p.to_dict()
        assert d["policy_id"] == "test"
        assert "delegation_min" in d


class TestTrustRelation:
    def test_to_dict(self) -> None:
        r = TrustRelation(
            local_agent_id="a1",
            remote_agent_id="a2",
            trust_level=TrustLevel.VERIFIED,
        )
        d = r.to_dict()
        assert d["local"] == "a1"
        assert d["trust"] == "verified"


# ============================================================================
# TrustNegotiator
# ============================================================================


class TestTrustNegotiator:
    def test_initiate(self) -> None:
        tn = TrustNegotiator()
        rel = tn.initiate("a1", "a2")
        assert rel.trust_level == TrustLevel.BASIC

    def test_verify_increases_trust(self) -> None:
        tn = TrustNegotiator()
        tn.initiate("a1", "a2")
        rel = tn.verify("a1", "a2")
        assert rel.trust_level == TrustLevel.VERIFIED

    def test_verify_nonexistent(self) -> None:
        tn = TrustNegotiator()
        assert tn.verify("a1", "a2") is None

    def test_verify_max_level(self) -> None:
        tn = TrustNegotiator()
        tn.initiate("a1", "a2")
        for _ in range(5):  # Upgrade to max
            tn.verify("a1", "a2")
        rel = tn.get_relation("a1", "a2")
        assert rel.trust_level == TrustLevel.PRIVILEGED

    def test_report_violation(self) -> None:
        tn = TrustNegotiator()
        tn.initiate("a1", "a2")
        tn.verify("a1", "a2")  # now VERIFIED
        rel = tn.report_violation("a1", "a2")
        assert rel.violations == 1
        assert rel.trust_level == TrustLevel.BASIC  # Downgraded

    def test_report_violation_three_resets_to_untrusted(self) -> None:
        tn = TrustNegotiator()
        tn.initiate("a1", "a2")
        tn.verify("a1", "a2")
        tn.verify("a1", "a2")
        for _ in range(3):
            tn.report_violation("a1", "a2")
        rel = tn.get_relation("a1", "a2")
        assert rel.trust_level == TrustLevel.UNTRUSTED

    def test_report_violation_nonexistent(self) -> None:
        tn = TrustNegotiator()
        assert tn.report_violation("a1", "a2") is None

    def test_can_delegate(self) -> None:
        tn = TrustNegotiator()
        assert tn.can_delegate("a1", "a2") is False
        tn.initiate("a1", "a2")
        tn.verify("a1", "a2")  # VERIFIED -- meets default policy
        assert tn.can_delegate("a1", "a2") is True

    def test_can_share_data(self) -> None:
        tn = TrustNegotiator()
        tn.initiate("a1", "a2")
        tn.verify("a1", "a2")  # VERIFIED
        assert tn.can_share_data("a1", "a2") is False  # Need TRUSTED
        tn.verify("a1", "a2")  # TRUSTED
        assert tn.can_share_data("a1", "a2") is True

    def test_get_relation(self) -> None:
        tn = TrustNegotiator()
        tn.initiate("a1", "a2")
        assert tn.get_relation("a1", "a2") is not None
        assert tn.get_relation("x", "y") is None

    def test_all_relations(self) -> None:
        tn = TrustNegotiator()
        tn.initiate("a1", "a2")
        tn.initiate("a3", "a4")
        assert len(tn.all_relations()) == 2

    def test_relation_count(self) -> None:
        tn = TrustNegotiator()
        assert tn.relation_count == 0
        tn.initiate("a1", "a2")
        assert tn.relation_count == 1

    def test_policy(self) -> None:
        tn = TrustNegotiator()
        assert tn.policy.policy_id == "default"

    def test_custom_policy(self) -> None:
        policy = TrustPolicy(
            policy_id="strict",
            min_trust_for_delegation=TrustLevel.PRIVILEGED,
        )
        tn = TrustNegotiator(policy=policy)
        assert tn.policy.min_trust_for_delegation == TrustLevel.PRIVILEGED

    def test_stats(self) -> None:
        tn = TrustNegotiator()
        tn.initiate("a1", "a2")
        stats = tn.stats()
        assert stats["total_relations"] == 1


# ============================================================================
# EmergencyController
# ============================================================================


class TestEmergencyController:
    def test_execute_lockdown(self) -> None:
        ec = EmergencyController()
        event = ec.execute(EmergencyAction.LOCKDOWN, "security breach")
        assert ec.is_lockdown is True
        assert event.event_id == "EMG-0001"

    def test_execute_kill_switch(self) -> None:
        ec = EmergencyController()
        ec.execute(EmergencyAction.KILL_SWITCH, "critical")
        assert ec.is_lockdown is True

    def test_execute_quarantine_agent(self) -> None:
        ec = EmergencyController()
        ec.execute(EmergencyAction.QUARANTINE_AGENT, "rogue", target="agent-1")
        assert ec.is_quarantined("agent-1") is True
        assert "agent-1" in ec.quarantined_agents

    def test_execute_quarantine_skill(self) -> None:
        ec = EmergencyController()
        ec.execute(EmergencyAction.QUARANTINE_SKILL, "dangerous", target="skill-x")
        assert ec.is_quarantined("skill-x") is True
        assert "skill-x" in ec.quarantined_skills

    def test_execute_rollback(self) -> None:
        ec = EmergencyController()
        ec.execute(EmergencyAction.LOCKDOWN, "test")
        ec.execute(EmergencyAction.QUARANTINE_AGENT, "test", target="a1")
        ec.execute(EmergencyAction.ROLLBACK, "restore")
        assert ec.is_lockdown is False
        assert not ec.quarantined_agents

    def test_revert_lockdown(self) -> None:
        ec = EmergencyController()
        event = ec.execute(EmergencyAction.LOCKDOWN, "test")
        assert ec.revert(event.event_id) is True
        assert ec.is_lockdown is False

    def test_revert_quarantine_agent(self) -> None:
        ec = EmergencyController()
        event = ec.execute(EmergencyAction.QUARANTINE_AGENT, "test", target="a1")
        ec.revert(event.event_id)
        assert ec.is_quarantined("a1") is False

    def test_revert_quarantine_skill(self) -> None:
        ec = EmergencyController()
        event = ec.execute(EmergencyAction.QUARANTINE_SKILL, "test", target="s1")
        ec.revert(event.event_id)
        assert ec.is_quarantined("s1") is False

    def test_revert_nonexistent(self) -> None:
        ec = EmergencyController()
        assert ec.revert("EMG-9999") is False

    def test_revert_already_reverted(self) -> None:
        ec = EmergencyController()
        event = ec.execute(EmergencyAction.LOCKDOWN, "test")
        ec.revert(event.event_id)
        assert ec.revert(event.event_id) is False

    def test_history(self) -> None:
        ec = EmergencyController()
        ec.execute(EmergencyAction.LOCKDOWN, "a")
        ec.execute(EmergencyAction.QUARANTINE_AGENT, "b", target="x")
        history = ec.history(limit=10)
        assert len(history) == 2
        # Most recent first
        assert history[0].reason == "b"

    def test_event_count(self) -> None:
        ec = EmergencyController()
        assert ec.event_count == 0
        ec.execute(EmergencyAction.LOCKDOWN, "test")
        assert ec.event_count == 1

    def test_stats(self) -> None:
        ec = EmergencyController()
        ec.execute(EmergencyAction.LOCKDOWN, "test")
        stats = ec.stats()
        assert stats["total_events"] == 1
        assert stats["lockdown_active"] is True

    def test_emergency_event_to_dict(self) -> None:
        e = EmergencyEvent(
            event_id="EMG-0001",
            action=EmergencyAction.LOCKDOWN,
            reason="test",
        )
        d = e.to_dict()
        assert d["action"] == "kill_switch" or d["action"] == "lockdown"


# ============================================================================
# MultiTenantGovernor
# ============================================================================


class TestMultiTenantGovernor:
    def test_init(self) -> None:
        gov = MultiTenantGovernor()
        assert gov.tenants is not None
        assert gov.trust is not None
        assert gov.emergency is not None

    def test_pre_action_check_ok(self) -> None:
        gov = MultiTenantGovernor()
        t = gov.tenants.create("Test", "a@b.com")
        result = gov.pre_action_check(t.tenant_id, "agent-1")
        assert result["allowed"] is True

    def test_pre_action_check_lockdown(self) -> None:
        gov = MultiTenantGovernor()
        t = gov.tenants.create("Test", "a@b.com")
        gov.emergency.execute(EmergencyAction.LOCKDOWN, "test")
        result = gov.pre_action_check(t.tenant_id, "agent-1")
        assert result["allowed"] is False
        assert "Lockdown" in result["reason"]

    def test_pre_action_check_quarantined_agent(self) -> None:
        gov = MultiTenantGovernor()
        t = gov.tenants.create("Test", "a@b.com")
        gov.emergency.execute(EmergencyAction.QUARANTINE_AGENT, "test", target="agent-1")
        result = gov.pre_action_check(t.tenant_id, "agent-1")
        assert result["allowed"] is False

    def test_pre_action_check_unknown_tenant(self) -> None:
        gov = MultiTenantGovernor()
        result = gov.pre_action_check("nonexistent", "agent-1")
        assert result["allowed"] is False

    def test_pre_action_check_suspended_tenant(self) -> None:
        gov = MultiTenantGovernor()
        t = gov.tenants.create("Test", "a@b.com")
        gov.tenants.suspend(t.tenant_id)
        result = gov.pre_action_check(t.tenant_id, "agent-1")
        assert result["allowed"] is False

    def test_stats(self) -> None:
        gov = MultiTenantGovernor()
        gov.tenants.create("Test", "a@b.com")
        stats = gov.stats()
        assert "tenants" in stats
        assert "trust" in stats
        assert "emergency" in stats
