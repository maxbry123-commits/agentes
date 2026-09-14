package engine

import (
	"context"
	"encoding/json"
	"os"
	"strconv"
	"time"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	"github.com/google/uuid"
)

// RunDemoReplay replays a real crAPI campaign entirely offline — no network, no
// LLM, no API key, no Docker. It emits the exact same CampaignEvent stream a
// live swarm run produces (recon endpoints, phase changes, attack chains, the
// exploit probe fan-out, graded findings, cost ticks), paced with small delays
// so both the terminal TUI and the web dashboard populate as if the swarm were
// running for real. Built for demos where venue wifi (or anything else) can't
// be trusted. It is API-compatible with Runner.RunSwarm so the CLI can swap it
// in behind --demo.
//
// Pacing scales with PENTESTSWARM_DEMO_SPEED (default 1.0; >1 is faster, e.g.
// 4 for a quick smoke test, 0.5 to slow it down on stage).
func RunDemoReplay(ctx context.Context, cc CampaignConfig, onEvent EventCallback) error {
	speed := 1.0
	if v := os.Getenv("PENTESTSWARM_DEMO_SPEED"); v != "" {
		if f, err := strconv.ParseFloat(v, 64); err == nil && f > 0 {
			speed = f
		}
	}
	campaignID := uuid.New()
	r := &demoReplayer{ctx: ctx, stop: cc.StopRequested, onEvent: onEvent, campaignID: campaignID, speed: speed}
	r.run()
	return nil
}

type demoReplayer struct {
	ctx        context.Context
	stop       <-chan struct{}
	onEvent    EventCallback
	campaignID uuid.UUID
	speed      float64
}

// wait sleeps for d (scaled by speed), returning false if the run was cancelled
// (TUI quit / context done) or the killswitch fired — so the demo stops
// promptly like a real run.
func (r *demoReplayer) wait(ms int) bool {
	d := time.Duration(float64(ms)/r.speed) * time.Millisecond
	t := time.NewTimer(d)
	defer t.Stop()
	select {
	case <-r.ctx.Done():
		return false
	case <-r.stop:
		return false
	case <-t.C:
		return true
	}
}

func (r *demoReplayer) emit(t pipeline.EventType, agent, detail string, data any) bool {
	ev := pipeline.CampaignEvent{
		ID:         uuid.New(),
		CampaignID: r.campaignID,
		Timestamp:  time.Now(),
		EventType:  t,
		AgentName:  agent,
		Detail:     detail,
	}
	if data != nil {
		ev.Data, _ = json.Marshal(data)
	}
	if r.onEvent != nil {
		r.onEvent(ev)
	}
	return true
}

// step emits an event then waits; returns false to abort the whole replay.
func (r *demoReplayer) step(delayMs int, t pipeline.EventType, agent, detail string, data any) bool {
	r.emit(t, agent, detail, data)
	return r.wait(delayMs)
}

func fMap(sev, title, cat string, cvss float64, conf, desc string) map[string]any {
	return map[string]any{"severity": sev, "title": title, "category": cat, "cvss": cvss, "confidence": conf, "description": desc}
}
func chainStarted(id, name string, steps ...[2]string) map[string]any {
	ss := make([]map[string]string, 0, len(steps))
	for _, s := range steps {
		ss = append(ss, map[string]string{"name": s[0], "technique": s[1]})
	}
	return map[string]any{"id": id, "name": name, "steps": ss}
}
func chainStep(id, step string, ok bool) map[string]any {
	return map[string]any{"chain_id": id, "step": step, "success": ok}
}
func probeData(target string, ok bool) map[string]any {
	return map[string]any{"target": target, "ok": ok}
}

func (r *demoReplayer) run() {
	const T = "crapi-demo.local"

	// ── Boot ──────────────────────────────────────────────────────────────
	if !r.step(500, pipeline.EventStateChange, "engine", "Swarm campaign initialized", nil) {
		return
	}
	if !r.step(700, pipeline.EventThought, "orchestrator", "Swarm deployed against "+T+" — seeding the blackboard", nil) {
		return
	}

	// ── Recon: map the attack surface ─────────────────────────────────────
	if !r.step(500, pipeline.EventStateChange, "recon", "recon agent scanning — mapping API surface", nil) {
		return
	}
	endpoints := []string{
		"http://" + T + "/",
		"/identity/api/auth/login",
		"/identity/api/v2/user/dashboard",
		"/identity/api/v2/vehicle/vehicles",
		"/identity/api/v2/vehicle/{vehicleId}/location",
		"/community/api/v2/community/posts/recent",
		"/community/api/v2/coupon/validate-coupon",
		"/workshop/api/shop/products",
		"/workshop/api/shop/orders/{orderId}",
		"/workshop/api/merchant/contact_mechanic",
		"/identity/api/v2/admin/videos/{videoId}",
	}
	if !r.step(400, pipeline.EventToolCall, "recon", "httpx — probing "+T+" (11 endpoints)", nil) {
		return
	}
	for _, e := range endpoints {
		if !r.step(180, pipeline.EventEndpointDiscovered, "recon", e, nil) {
			return
		}
	}
	if !r.step(600, pipeline.EventToolResult, "recon", "nuclei — 11 endpoints fingerprinted (Node/Java/Python services)", nil) {
		return
	}

	// ── Classify: grade the surface ───────────────────────────────────────
	if !r.step(500, pipeline.EventStateChange, "classifier", "classifier grading discovered surface by severity", nil) {
		return
	}
	if !r.step(900, pipeline.EventThought, "classifier", "11 endpoints scored · flagging object-id and auth surfaces for exploitation", nil) {
		return
	}

	// ── Plan + Execute: the swarm builds and runs attack chains ───────────
	if !r.step(500, pipeline.EventStateChange, "exploit", "planning attack chains from graded findings", nil) {
		return
	}
	if !r.step(700, pipeline.EventStateChange, "exploit", "executing chains — swarm fanning out", nil) {
		return
	}

	// Chain 1 — BOLA vehicle location (+ probe fan-out + finding).
	c1 := uuid.NewString()
	if !r.step(500, pipeline.EventChainStarted, "exploit", "BOLA — cross-user vehicle location", chainStarted(c1,
		"BOLA — cross-user vehicle location",
		[2]string{"authenticate as victim", "T1078"},
		[2]string{"read own vehicle id", "API1:2023"},
		[2]string{"harvest foreign object id", "API1:2023"},
		[2]string{"replay foreign vehicle id", "API1:2023"})) {
		return
	}
	if !r.step(450, pipeline.EventChainStep, "exploit", "authenticate as victim", chainStep(c1, "authenticate as victim", true)) {
		return
	}
	if !r.step(450, pipeline.EventChainStep, "exploit", "read own vehicle id", chainStep(c1, "read own vehicle id", true)) {
		return
	}
	if !r.step(450, pipeline.EventChainStep, "exploit", "harvest foreign object id", chainStep(c1, "harvest foreign object id", true)) {
		return
	}
	// Probe fan-out — replay harvested ids across the id-bearing endpoint.
	r.probeBurst("/identity/api/v2/vehicle/", "/location", 34, 3)
	if r.aborted() {
		return
	}
	if !r.step(500, pipeline.EventChainStep, "exploit", "replay foreign vehicle id", chainStep(c1, "replay foreign vehicle id", true)) {
		return
	}
	if !r.step(900, pipeline.EventFindingDiscovered, "exploit", "BOLA: another user's vehicle location",
		fMap("high", "BOLA — another user's live vehicle location", "broken_object_level_authorization", 8.1, "high",
			"The swarm harvested a vehicle UUID belonging to another user from an earlier response and replayed it at "+
				"/identity/api/v2/vehicle/{id}/location with its own session. The endpoint returned 200 with the victim's "+
				"live GPS coordinates — broken object-level authorization (OWASP API1:2023).")) {
		return
	}

	// Chain 2 — NoSQL injection in coupon validation.
	c2 := uuid.NewString()
	if !r.step(500, pipeline.EventChainStarted, "exploit", "NoSQL injection — coupon validation", chainStarted(c2,
		"NoSQL injection — coupon validation",
		[2]string{"authenticate", "T1078"},
		[2]string{"POST validate-coupon {\"$ne\":null}", "T1190"},
		[2]string{"confirm coupon accepted", "T1190"})) {
		return
	}
	if !r.step(450, pipeline.EventChainStep, "exploit", "authenticate", chainStep(c2, "authenticate", true)) {
		return
	}
	if !r.step(500, pipeline.EventChainStep, "exploit", "POST validate-coupon {\"$ne\":null}", chainStep(c2, "POST validate-coupon {\"$ne\":null}", true)) {
		return
	}
	if !r.step(500, pipeline.EventChainStep, "exploit", "confirm coupon accepted", chainStep(c2, "confirm coupon accepted", true)) {
		return
	}
	if !r.step(400, pipeline.EventMilestone, "cost", "spent $0.31 so far (142310 in / 0 cached / 8120 out)", nil) {
		return
	}
	if !r.step(900, pipeline.EventFindingDiscovered, "exploit", "NoSQL injection in coupon validation",
		fMap("high", "NoSQL injection — coupon validation bypass", "injection", 7.5, "high",
			"POST /community/api/v2/coupon/validate-coupon with {\"coupon_code\":{\"$ne\":null}} returns a valid coupon. "+
				"The MongoDB $ne operator is interpolated into the query unsanitised, bypassing coupon validation entirely.")) {
		return
	}

	// Chain 3 — Excessive data exposure in the community feed.
	c3 := uuid.NewString()
	if !r.step(500, pipeline.EventChainStarted, "exploit", "Excessive data exposure — community feed", chainStarted(c3,
		"Excessive data exposure — community feed",
		[2]string{"GET /community/api/v2/community/posts/recent", "API3:2023"},
		[2]string{"extract PII from response", "API3:2023"})) {
		return
	}
	if !r.step(450, pipeline.EventChainStep, "exploit", "GET /community/api/v2/community/posts/recent", chainStep(c3, "GET /community/api/v2/community/posts/recent", true)) {
		return
	}
	if !r.step(500, pipeline.EventChainStep, "exploit", "extract PII from response", chainStep(c3, "extract PII from response", true)) {
		return
	}
	if !r.step(850, pipeline.EventFindingDiscovered, "exploit", "Excessive data exposure: community feed PII",
		fMap("medium", "Excessive data exposure — PII in community feed", "excessive_data_exposure", 5.3, "high",
			"GET /community/api/v2/community/posts/recent returns other users' PII — email addresses and vehicle IDs — "+
				"far beyond what the feed UI renders. Classic excessive data exposure (OWASP API3:2023).")) {
		return
	}

	// Chain 4 — JWT forgery → account takeover (the headline finding).
	c4 := uuid.NewString()
	if !r.step(500, pipeline.EventChainStarted, "exploit", "JWT forgery — account takeover", chainStarted(c4,
		"JWT forgery — account takeover",
		[2]string{"decode session JWT", "T1552"},
		[2]string{"forge alg:none admin token", "T1548"},
		[2]string{"access admin dashboard", "T1078.004"})) {
		return
	}
	if !r.step(450, pipeline.EventChainStep, "exploit", "decode session JWT", chainStep(c4, "decode session JWT", true)) {
		return
	}
	if !r.step(500, pipeline.EventChainStep, "exploit", "forge alg:none admin token", chainStep(c4, "forge alg:none admin token", true)) {
		return
	}
	if !r.step(400, pipeline.EventMilestone, "cost", "spent $0.66 so far (301884 in / 0 cached / 17740 out)", nil) {
		return
	}
	if !r.step(600, pipeline.EventChainStep, "exploit", "access admin dashboard", chainStep(c4, "access admin dashboard", true)) {
		return
	}
	if !r.step(1000, pipeline.EventFindingDiscovered, "exploit", "JWT alg:none accepted → account takeover",
		fMap("critical", "JWT alg:none accepted — full account takeover", "broken_authentication", 9.8, "high",
			"The API accepts a JWT signed with alg:none (and separately the weak HS256 secret \"crapi\"). The swarm forged "+
				"a token with the victim's sub and role=admin; /identity/api/v2/admin returned 200. Complete authentication "+
				"bypass and account takeover (OWASP API2:2023).")) {
		return
	}

	// ── Report ────────────────────────────────────────────────────────────
	if !r.step(700, pipeline.EventStateChange, "report", "report agent — assembling graded findings + evidence", nil) {
		return
	}
	if !r.step(900, pipeline.EventMilestone, "cost", "total spent $0.87  (input 372014, cached 0, output 21993)", nil) {
		return
	}
	r.step(200, pipeline.EventMilestone, "orchestrator", "Swarm campaign complete — 4 findings (1 critical, 2 high, 1 medium) — see ./reports", nil)
}

// probeBurst emits a fast spray of BOLA probe events (the exploit fan-out): n
// replays of harvested ids across an id-bearing endpoint, of which `hits` land
// (200). Mostly misses, like a real sweep.
func (r *demoReplayer) probeBurst(prefix, suffix string, n, hits int) {
	hitAt := map[int]bool{}
	if n > 0 {
		hitAt[n/5] = true
		hitAt[n/2] = true
		hitAt[(n*4)/5] = true
	}
	_ = hits
	for i := 0; i < n; i++ {
		id := demoVehicleIDs[i%len(demoVehicleIDs)]
		ok := hitAt[i]
		if !r.step(85, pipeline.EventProbe, "exploit", prefix+id+suffix, probeData(prefix+id+suffix, ok)) {
			return
		}
	}
}

func (r *demoReplayer) aborted() bool {
	select {
	case <-r.ctx.Done():
		return true
	case <-r.stop:
		return true
	default:
		return false
	}
}

// demoVehicleIDs are plausible object UUIDs the fan-out "replays". Static so the
// demo is deterministic.
var demoVehicleIDs = []string{
	"4bafdcc2-8b6b-4f1a-9d1e-2f2a1e7c9a01", "9c1e77aa-3d21-4c88-b0f2-6a5d0e2b7c3d",
	"e2b4a1d9-77c3-4a10-8f6b-1c9e3d5a2f80", "1a7f0c93-6e2d-4b55-9a3c-8d4e1f6b0a22",
	"7d3e9b41-2c8a-4f60-b1d7-3e9c6a2b5d14", "b58c2e07-9a1f-4d3b-8c6e-2a7f1d0b9e46",
	"3f9a1c68-4b2d-4e70-9f1a-6c8b3d2e7a05", "c6d2b93e-1f7a-4c48-b9e2-5a3d8f1c0b67",
}
