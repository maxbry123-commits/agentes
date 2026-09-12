"""YAIWES AG2 STEP3 adapter: real AG2 Network workflow through canonical FABLES bus."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

PLUGIN_ID = "yaiwes.agent_fleet.ag2"
ROLE = "multi_agent_workflow_orchestration"
TARGET_RELATIVE = "Agente Yaiwes principal/agent-fleet-parallelism/ag2"


def descriptor() -> dict[str, str]:
    return {
        "plugin_id": PLUGIN_ID,
        "role": ROLE,
        "target_path": TARGET_RELATIVE,
        "microtest": "bridge_drives_workflow_alice_bob_alice",
    }


async def _scenario() -> dict[str, Any]:
    from ag2.knowledge import MemoryKnowledgeStore
    from ag2.network import (
        AgentTarget,
        FromSpeaker,
        Handoff,
        Hub,
        HubClient,
        LocalLink,
        Passport,
        Resume,
        RevertToInitiatorTarget,
        TerminateTarget,
        Transition,
        TransitionGraph,
        WorkflowState,
    )
    from ag2.network.adapters.workflow import WORKFLOW_TYPE
    from ag2.network.channel import ChannelState

    store = MemoryKnowledgeStore()
    hub = await Hub.open(store, ttl_sweep_interval=0)
    link = LocalLink(hub)
    alice_hc = HubClient(link, hub=hub)
    bob_hc = HubClient(link, hub=hub)
    try:
        alice = await alice_hc.register_human(Passport(name="alice"), resume=Resume())
        bob = await bob_hc.register_human(Passport(name="bob"), resume=Resume())
        graph = TransitionGraph(
            initial_speaker=alice.agent_id,
            transitions=[
                Transition(when=FromSpeaker(alice.agent_id), then=AgentTarget(bob.agent_id)),
                Transition(when=FromSpeaker(bob.agent_id), then=RevertToInitiatorTarget()),
            ],
            default_target=TerminateTarget(reason="yaiwes_ag2_bridge_done"),
            max_turns=8,
        )
        channel = await alice.open(
            type=WORKFLOW_TYPE,
            target=[bob.agent_id],
            knobs={"graph": graph.to_dict()},
        )
        if channel.state != ChannelState.ACTIVE:
            raise RuntimeError(f"AG2_CHANNEL_NOT_ACTIVE:{channel.state}")
        adapter = hub.adapter_for(channel.channel_id)
        env_alice = adapter.build_packet_envelope(
            channel_id=channel.channel_id,
            sender_id=alice.agent_id,
            body="alice opens the discussion",
        )
        await hub.post_envelope(env_alice)
        state1 = hub.adapter_state(channel.channel_id)
        if not isinstance(state1, WorkflowState) or state1.expected_next_speaker != bob.agent_id:
            raise RuntimeError(f"AG2_ALICE_TO_BOB_FAILED:{state1}")
        env_bob = adapter.build_packet_envelope(
            channel_id=channel.channel_id,
            sender_id=bob.agent_id,
            body="bob replies",
            handoff=Handoff(target=alice.agent_id, reason="back to you"),
        )
        await hub.post_envelope(env_bob)
        state2 = hub.adapter_state(channel.channel_id)
        if state2.expected_next_speaker != alice.agent_id:
            raise RuntimeError(f"AG2_BOB_TO_ALICE_FAILED:{state2}")
        return {
            "status": "PASS",
            "capability": "ag2_network_workflow_handoff",
            "route": ["alice", "bob", "alice"],
            "channel_state": str(channel.state.value),
            "last_speaker": "bob",
        }
    finally:
        await alice_hc.close()
        await bob_hc.close()
        await hub.close()


def run_microtest(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    target = root / TARGET_RELATIVE
    if not (target / "ag2" / "network").is_dir():
        raise RuntimeError(f"AG2_NETWORK_MISSING:{target}")
    if str(target) not in sys.path:
        sys.path.insert(0, str(target))
    return asyncio.run(_scenario())


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: ag2_adapter.py <repo_root>")
    result = run_microtest(sys.argv[1])
    print("YAIWES_AG2_RESULT=" + json.dumps(result, separators=(",", ":")), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
