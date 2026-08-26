# BLOCKER-T-GAP — G5

**Problem:** No verified p01_* … p12_* source set is available in `main`.

**Source evidence:** repository search found the PASO3/ORIGIN_MAP references and the canonical target placeholder, but no complete twelve-stage source implementation.

**Impact:** An end-to-end p01→p12 implementation cannot be generated without inventing twelve modules or changing the hot path.

**Recommended action:** acquire/restore the real `programming-modular-v1` source set, then repeat Refactoria source→new→3-way verification and parity tests before integration.

**Status:** BLOCKED. No fake implementation created.
