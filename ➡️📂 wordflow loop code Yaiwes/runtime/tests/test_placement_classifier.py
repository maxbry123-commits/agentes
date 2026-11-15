from runtime.src.core.placement_classifier import PlacementRequest, classify_placement


def test_all_primary_destinations_and_review_gate():
    cases = [
        (PlacementRequest("scheduler", privileged=True, kernel_invariant=True, lifecycle="process", execution="core"), "A_KERNEL"),
        (PlacementRequest("plugin", privileged=True, lifecycle="persistent", execution="extension"), "B_EXTENSION_KERNEL"),
        (PlacementRequest("council", reasoning=True, execution="reasoning"), "C_REASONING_LAYER"),
        (PlacementRequest("agent-step", agent_chain=True, lifecycle="task", execution="workflow"), "D_WORDFLOW"),
        (PlacementRequest("workers", fanout=True, execution="pool", stateful=True), "E_POOL"),
        (PlacementRequest("git-adapter", reusable_tool=True, external_io=True, execution="tool"), "F_TOOLS"),
        (PlacementRequest("telemetry", execution="other", other_location="observability", other_justification="cross-cutting telemetry"), "G_OTHER"),
        (PlacementRequest("ambiguous", reasoning=True, agent_chain=True), "PLACEMENT_REVIEW_REQUIRED"),
    ]
    for request, expected in cases:
        decision = classify_placement(request)
        assert decision.placement == expected
        assert decision.reason_codes


def test_weak_signal_fails_closed():
    decision = classify_placement(PlacementRequest("unknown"))
    assert decision.placement == "PLACEMENT_REVIEW_REQUIRED"
    assert decision.reason_codes == ("INSUFFICIENT_OR_CONFLICTING_SIGNALS",)


def test_other_requires_explicit_justification():
    decision = classify_placement(PlacementRequest("custom", execution="other", other_location="custom-layer"))
    assert decision.placement == "PLACEMENT_REVIEW_REQUIRED"
    assert decision.reason_codes == ("OTHER_REQUIRES_LOCATION_AND_JUSTIFICATION",)
