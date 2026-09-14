"""Tests for the state machine."""

import pytest
from src.state import AgentState, Phase, PhaseResult, CommandRecord


class TestPhaseTransitions:
    def test_phase_order(self):
        assert Phase.INIT.next_phase == Phase.RECON
        assert Phase.RECON.next_phase == Phase.ENUMERATION
        assert Phase.ENUMERATION.next_phase == Phase.EXPLOIT
        assert Phase.EXPLOIT.next_phase == Phase.PRIVESC
        assert Phase.PRIVESC.next_phase == Phase.LOOT
        assert Phase.LOOT.next_phase == Phase.COMPLETE
        assert Phase.COMPLETE.next_phase is None

    def test_advance_phase(self):
        state = AgentState(target_ip="10.10.10.56", machine_name="Shocker")
        state.current_phase = Phase.RECON

        result = PhaseResult(phase=Phase.RECON, success=True, findings=["port 80 open"])
        state.advance_phase(result)

        assert state.current_phase == Phase.ENUMERATION
        assert len(state.phases_completed) == 1


class TestAgentState:
    def test_add_command(self):
        state = AgentState(target_ip="10.10.10.56", machine_name="Shocker")
        state.current_phase = Phase.RECON

        record = CommandRecord(command="nmap -sV 10.10.10.56", output="80/tcp open http", exit_code=0)
        state.add_command(record)

        assert state.total_commands == 1
        assert state.command_history[0].phase == "recon"

    def test_context_summary(self):
        state = AgentState(target_ip="10.10.10.56", machine_name="Shocker")
        state.open_ports.append({"port": 80, "service": "http", "details": "Apache 2.4.18"})

        summary = state.get_context_summary()
        assert "10.10.10.56" in summary
        assert "80" in summary