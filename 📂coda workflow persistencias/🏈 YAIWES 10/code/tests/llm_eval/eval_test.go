package llm_eval

import (
	"context"
	"strings"
	"testing"
	"time"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/agent/classifier"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	"github.com/google/uuid"
)

func TestClassifierFixtures(t *testing.T) {
	fixtures, err := LoadFixtures("fixtures")
	if err != nil {
		t.Fatal(err)
	}
	if len(fixtures) == 0 {
		t.Fatal("no fixtures loaded")
	}

	for _, fx := range fixtures {
		fx := fx
		t.Run(fx.Name, func(t *testing.T) {
			if fx.Agent != "classifier" {
				t.Skipf("skipping non-classifier fixture: %s", fx.Agent)
			}

			// Build classifier with the canned mock provider.
			provider := NewMockProvider(fx.MockResponse)
			agent := classifier.NewClassifierAgent(provider)

			// Build input findings from the fixture.
			var raw []pipeline.RawFinding
			inputs, _ := fx.Input["findings"].([]any)
			for _, it := range inputs {
				m, _ := it.(map[string]any)
				raw = append(raw, pipeline.RawFinding{
					ID:           uuid.New(),
					CampaignID:   uuid.Nil,
					Source:       asString(m, "source"),
					Type:         asString(m, "type"),
					Target:       asString(m, "target"),
					Detail:       asString(m, "detail"),
					DiscoveredAt: time.Now(),
				})
			}

			set, err := agent.Classify(context.Background(), uuid.New(), raw)
			if err != nil {
				t.Fatalf("classifier: %v", err)
			}
			if len(set.Findings) == 0 {
				t.Fatal("classifier returned no findings")
			}

			// Rubric is checked against the first classified finding; if
			// future fixtures need multi-finding rubrics we can extend.
			got := set.Findings[0]
			if fails := fx.Rubric.Check(got); len(fails) > 0 {
				t.Fatalf("rubric failed:\n  - %s\n  classified: %+v",
					strings.Join(fails, "\n  - "), got)
			}
		})
	}
}

func asString(m map[string]any, k string) string {
	if v, ok := m[k]; ok {
		if s, ok := v.(string); ok {
			return s
		}
	}
	return ""
}
