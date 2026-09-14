package ui

import (
	"strings"
	"testing"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
)

// A probe event must bump the probes tally, light the exploit fan, and surface
// a "probes N" counter in the live counters row — the terminal echo of the
// dashboard's fan-out mesh.
func TestProbeEventsRenderFanAndCounter(t *testing.T) {
	m := NewModel("cid", "target.example", "find bugs")
	m.width = 100 // wide enough for the full counters row + fan

	const n = 7
	for i := 0; i < n; i++ {
		m.handleEvent(pipeline.CampaignEvent{
			EventType: pipeline.EventProbe,
			AgentName: "exploit",
			Detail:    "http://target.example/vehicle/42/location",
		})
	}

	if m.probes != n {
		t.Fatalf("expected probes tally %d, got %d", n, m.probes)
	}

	view := stripANSI(m.View())
	if !strings.Contains(view, "probes 7") {
		t.Fatalf("counters row should show 'probes 7', got:\n%s", view)
	}
	if !strings.Contains(view, "EXPLOIT") {
		t.Fatalf("view should render the EXPLOIT node/fan, got:\n%s", view)
	}
}

// ExploitFan is empty before any probe and non-empty once probes exist, so the
// idle view is unchanged.
func TestExploitFan(t *testing.T) {
	if got := ExploitFan(0, 0, 80); got != "" {
		t.Errorf("no probes: expected empty fan, got %q", got)
	}
	fan := stripANSI(ExploitFan(4, 12, 80))
	if !strings.Contains(fan, "EXPLOIT") || !strings.Contains(fan, "12 probes") {
		t.Errorf("active fan should label the EXPLOIT node and probe count, got %q", fan)
	}
}

// A wide run driven through surface, probes, findings and a spend milestone
// must render every new telemetry panel — the swarm cluster (not the old
// stacked boxes), the sparkline traces, the risk gauge and the spend meter —
// plus the animated blackboard core with its live item count.
func TestUpgradedPanelsRenderLive(t *testing.T) {
	m := NewModel("cid", "crapi.example", "find BOLA/IDOR")
	m.width = 130
	m.height = 50

	m.handleEvent(pipeline.CampaignEvent{EventType: pipeline.EventStateChange, Detail: "recon phase"})
	for i := 0; i < 6; i++ {
		m.handleEvent(pipeline.CampaignEvent{EventType: pipeline.EventEndpointDiscovered, AgentName: "recon", Detail: "/x"})
	}
	m.handleEvent(pipeline.CampaignEvent{EventType: pipeline.EventStateChange, Detail: "execute phase"})
	for i := 0; i < 10; i++ {
		m.handleEvent(pipeline.CampaignEvent{EventType: pipeline.EventProbe, AgentName: "exploit", Detail: "/vehicle/42/location"})
	}
	m.handleEvent(pipeline.CampaignEvent{
		EventType: pipeline.EventFindingDiscovered, Detail: "BOLA",
		Data: []byte(`{"severity":"critical","title":"BOLA on vehicle location"}`),
	})
	m.handleEvent(pipeline.CampaignEvent{
		EventType: pipeline.EventMilestone, AgentName: "cost",
		Detail: "spent $0.184 so far (100 in / 20 cached / 40 out)",
	})

	// Drive several ticks so the time-series fill and the animation advances.
	for tk := 0; tk < 8; tk++ {
		m.frame++
		m.sampleSeries()
		if tk%2 == 0 {
			m.probes += 2
		}
	}

	if m.spend != 0.184 {
		t.Fatalf("cost milestone should set spend to 0.184, got %v", m.spend)
	}

	view := stripANSI(m.View())
	wants := []string{
		"SWARM",           // the swarm-cluster panel header
		"TELEMETRY",       // the charts panel header
		"surface",         // attack-surface sparkline row
		"probes",          // probe-throughput sparkline row
		"finds",           // findings-over-time sparkline row
		"risk score",      // composite risk gauge
		"CRITICAL",        // risk band label (a critical finding landed)
		"spend vs budget", // spend meter
		"$0.184",          // parsed spend rendered on the meter
		"activity",        // per-agent activity bars
		"blackboard",      // animated blackboard core
		"live items",      // core's live item count
	}
	for _, w := range wants {
		if !strings.Contains(view, w) {
			t.Errorf("upgraded view missing %q\n--- view ---\n%s", w, view)
		}
	}

	// The old sequential stacked-box layout ("Agents" heading) must be gone,
	// replaced by decentralized swarm imagery.
	if strings.Contains(view, " Agents") {
		t.Errorf("expected the stacked agent boxes to be replaced by swarm imagery, but found the old 'Agents' panel")
	}
}

// The telemetry sparklines must show motion from surface/probe growth even
// before any finding lands, so the early wait is visibly alive.
func TestTelemetryMovesBeforeFindings(t *testing.T) {
	m := NewModel("cid", "t", "o")
	m.width = 130
	m.height = 50
	for i := 0; i < 4; i++ {
		m.handleEvent(pipeline.CampaignEvent{EventType: pipeline.EventEndpointDiscovered, AgentName: "recon"})
	}
	for i := 0; i < 5; i++ {
		m.handleEvent(pipeline.CampaignEvent{EventType: pipeline.EventProbe, AgentName: "exploit"})
	}
	for tk := 0; tk < 5; tk++ {
		m.frame++
		m.sampleSeries()
	}
	if len(m.findings) != 0 {
		t.Fatalf("precondition: expected no findings")
	}
	sum := func(s []int) (t int) {
		for _, v := range s {
			t += v
		}
		return
	}
	if sum(m.surfaceSeries) == 0 || sum(m.probeSeries) == 0 {
		t.Fatalf("surface/probe series should show motion before findings: surface=%v probes=%v",
			m.surfaceSeries, m.probeSeries)
	}
}

// parseSpend pulls the dollar figure out of the cost-milestone detail strings.
func TestParseSpend(t *testing.T) {
	cases := map[string]float64{
		"spent $0.184 so far (100 in / 20 cached / 40 out)":    0.184,
		"total spent $1.20 (input 100, cached 5, output 9)":    1.20,
		"cost cap $2.00 reached (spent $1.999) — winding down": 2.00,
	}
	for in, want := range cases {
		got, ok := parseSpend(in)
		if !ok || got != want {
			t.Errorf("parseSpend(%q) = %v, %v; want %v", in, got, ok, want)
		}
	}
	if _, ok := parseSpend("no dollars here"); ok {
		t.Errorf("parseSpend should fail when there is no $ figure")
	}
}
