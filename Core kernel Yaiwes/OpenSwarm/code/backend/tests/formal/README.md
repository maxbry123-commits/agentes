# Formal proofs

Machine-checked proofs of safety/security invariants that the unit/property
tests can only *sample*. A property test tries thousands of cases; an SMT proof
is exhaustive over the modeled domain (assert the negation, `unsat` => theorem).

Not wired into prod or CI, and excluded from the packaged build (under `tests/`).
Run manually:

```
pip install z3-solver
python backend/tests/formal/mcp_gate_proof.py
```

- **`mcp_gate_proof.py`** , the MCP dispatch-gate invariant (`agent_manager._build_mcp_servers`):
  a gated session forwards a server *only if* it was activated, an empty
  activation list forwards zero, and a denied server is never forwarded. Sampled
  by `tests/test_v2_invariants.py::test_mcp_gate_only_forwards_activated_servers`;
  proven for all inputs here. The script also refutes a deliberately-buggy gate
  (activation check dropped) so the proof can't be vacuous.
