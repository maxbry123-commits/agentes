package blackboard

import (
	"context"
	"strings"
	"testing"

	"github.com/google/uuid"
)

// MINJA-style memory injection tests (Phase 3.4.2).
//
// MINJA (arXiv:2503.03704) shows that agents which read shared memory
// can be tricked when an attacker plants a payload that *looks like*
// a high-confidence finding. The blackboard's defenses, in priority order:
//
//   1. Agents query by Type — payloads written under a type the
//      attacker doesn't anticipate are simply not retrieved.
//   2. Agents filter by MinPheromone — the attacker has to win the
//      decay race to be visible.
//   3. The pheromone clamp keeps malicious 'PheromoneBase: 1000' from
//      acting as a permanent signal.
//   4. Agent-name impersonation is detected at the provenance layer
//      (see internal/swarm/provenance) — out of scope for blackboard
//      tests but the threat model assumes that's wired upstream.
//
// These tests pin the behaviors above so a regression that, e.g.,
// silently accepts a 1000.0 pheromone value or returns wrong-type
// findings to a query gets flagged in CI.

func TestMINJA_QueryByTypeIsolatesPayload(t *testing.T) {
	b := NewMemoryBoard(nil)
	ctx := context.Background()
	camp := uuid.New()

	// Attacker plants a fake finding under a synthetic type the legit
	// recon agent will never query for.
	_, _ = b.Write(ctx, Finding{
		CampaignID: camp,
		AgentName:  "recon",
		Type:       "ATTACKER_INJECTED_PSEUDO_TYPE",
		Target:     "victim.example.com",
		Data:       []byte(`{"payload":"pretend i am a CVE_MATCH"}`),
	})
	// Legit classifier finding under the real type.
	_, _ = b.Write(ctx, Finding{
		CampaignID: camp,
		AgentName:  "classifier",
		Type:       TypeCVEMatch,
		Target:     "victim.example.com",
		Data:       []byte(`{"cve":"CVE-2024-1234"}`),
	})

	// Exploit agent queries for CVE_MATCH only.
	results, _ := b.Query(ctx, Predicate{Types: []FindingType{TypeCVEMatch}})
	if len(results) != 1 {
		t.Fatalf("expected exactly 1 CVE_MATCH, got %d", len(results))
	}
	if !strings.Contains(string(results[0].Data), "CVE-2024-1234") {
		t.Errorf("legitimate finding was lost; got %s", string(results[0].Data))
	}
}

func TestMINJA_PheromoneFloodIsClamped(t *testing.T) {
	b := NewMemoryBoard(nil)
	ctx := context.Background()
	camp := uuid.New()

	// Attacker tries to set pheromone way above the legitimate range to
	// dominate ranking. Either the board must clamp to 1.0 or refuse.
	id, _ := b.Write(ctx, Finding{
		CampaignID:    camp,
		AgentName:     "recon",
		Type:          TypeCVEMatch,
		Target:        "victim",
		PheromoneBase: 9999.0,
		HalfLifeSec:   3600,
	})
	results, _ := b.Query(ctx, Predicate{Types: []FindingType{TypeCVEMatch}})
	var got float64
	for _, r := range results {
		if r.ID == id {
			got = r.Pheromone
		}
	}
	if got > 1.0 {
		t.Errorf("pheromone-flood not clamped: got %f, want ≤ 1.0", got)
	}
}

func TestMINJA_MinPheromoneFiltersStaleInjection(t *testing.T) {
	b := NewMemoryBoard(nil)
	ctx := context.Background()
	camp := uuid.New()

	// Attacker writes a fake "high-confidence" finding but with a tiny
	// pheromone (e.g. confused about scale). Defenders that gate on
	// MinPheromone≥0.5 should skip it.
	_, _ = b.Write(ctx, Finding{
		CampaignID:    camp,
		AgentName:     "recon",
		Type:          TypeCVEMatch,
		Target:        "victim",
		PheromoneBase: 0.05,
		HalfLifeSec:   3600,
	})
	// Genuine high-confidence finding from the classifier.
	_, _ = b.Write(ctx, Finding{
		CampaignID:    camp,
		AgentName:     "classifier",
		Type:          TypeCVEMatch,
		Target:        "victim",
		PheromoneBase: 0.9,
		HalfLifeSec:   3600,
	})
	results, _ := b.Query(ctx, Predicate{
		Types:        []FindingType{TypeCVEMatch},
		MinPheromone: 0.5,
	})
	if len(results) != 1 {
		t.Errorf("expected only the high-confidence finding to survive MinPheromone gate, got %d", len(results))
	}
}
